# Documentos PROEX

> Emite la documentación de exportación de cada embarque (certificados de origen y sanitario, BL, DUA, waiver, factura/packing/carta de porte) y controla su ciclo de envío y recepción al cliente.

**Asistente 4 de 4** del flujo PROEX · Card CRM + Microservicio

## 📌 Rol en el flujo PROEX

Documentos es la última fase del ciclo comercial. Se activa cuando un Negocio Pedido llega a la etapa terminal **"Preparar Documentación"** del pipeline de Pedidos (`725914649`, dealstage `1368383244`): un webhook crea un **Negocio Documento 1:1 por contenedor** (pipeline `905179456`) que actúa como tracker de la fase.

- **Recibe de Pedidos (upstream):** los Contenedores ya facturados/en curso, con su cabecera logística (consignee, notify, shipper, puertos, almacén) que se replica al Negocio Documento, y la lista autoritativa `documentos_a_generar` por contenedor.
- **Lee de Cotizador (upstream):** las propiedades del deal cotización padre (descripción de mercancía, puertos, almacén) para componer los payloads de los certificados.
- **Lee de SAP (indirecto, solo lectura):** `numero_de_factura` y `fecha_de_vencimiento_factura` que SAP escribe en el pedido-deal; se muestran por contenedor pero el servicio nunca escribe hacia SAP.
- **Entrega:** los PDFs oficiales subidos al File Manager de HubSpot y el estado de documentación consolidado en el objeto **Contenedor** (source of truth). No hay asistente aguas abajo: aquí termina el pipeline con la mercancía retirada.

```
 Cotizador (1)      Cobros/Pagos (2)      Pedidos (3)         ┌──────────────────────┐
   Deal        →       Deal          →      Company     ──►   │   Documentos (4)     │ ◄── ESTE
 configura         reparte cobros       webhook: 1 deal       │   Company            │
 la oferta         por contenedor       Pedido/contenedor     │ certificados + BL +  │
                                        al ganar              │ envío al cliente     │
                                                              └──────────────────────┘
```

## 🏗️ Arquitectura

Dos piezas siguiendo el molde común de PROEX: una **card React (HubSpot UI Extensions)** montada como pestaña en la ficha de **Company**, y un **microservicio FastAPI** desplegado como imagen Docker en **AWS Lambda** detrás de **API Gateway HTTP API**. La card nunca llama a la API pública de HubSpot: toda lectura/escritura de CRM, ficheros y HubDB pasa por el microservicio vía `hubspot.fetch`.

A diferencia de Cotizador y Pedidos, este asistente es **100% síncrono**: no hay worker, cola SQS ni DLQ. Los endpoints `async` envuelven el SDK bloqueante de HubSpot con `asyncio.to_thread`, y la generación de PDFs vive dentro del timeout de 30 s de Lambda.

```
HubSpot CRM  (ficha de Company)
   │  Card React / UI Extensions — 3 tabs (Pendientes / Histórico / Gestión)
   │  hubspot.fetch  (HTTPS, único backend permitido)
   ▼
API Gateway HTTP API   (eu-south-2, payload v2.0, CORS *)
   ▼
AWS Lambda (imagen Docker)  ──  FastAPI 0.115 + Mangum  [función proex-documents]
   │
   ├─► HubSpot CRM  (SDK hubspot-api-client)   deals, Contenedor, Elemento, companies, assoc v4
   ├─► HubSpot Files v3  (REST con requests)   upload/delete/metadata → /documentos-proex/{...}
   └─► HubSpot HubDB                           formato_producto (traducción ES/EN/FR)
```

- **Card:** React 18 + TypeScript + `@hubspot/ui-extensions`, bundler Vite (HubSpot CLI), platform version 2025.2.
- **Microservicio:** Python 3.11, FastAPI + Uvicorn, Pydantic 2, `hubspot-api-client` 11, `reportlab` + `pypdf` + Pillow para el render de PDF.

## 📦 Componentes

### `documentos-proex-card/` — Tarjeta CRM (frontend)

Extensión de UI de HubSpot montada sobre **companies** (`card-hsmeta.json`: `crm.record.tab`, `objectTypes: ["companies"]`). Tres pestañas:

1. **Pendientes** — genera certificados (Origen borrador, Origen final, Sanitario) en ES/EN/FR con filtros SAP-like (empresa + tipos de documento + rangos ETD/ETA).
2. **Histórico** — lista lo generado y permite rollback controlado por grupo de generación.
3. **Gestión de documentación** — gestión integral por embarque: BL, certificados, DUA, waiver, factura/packing/carta de porte (readonly), otros documentos, fotos de carga, cobro y envío/recepción al cliente.

El modelo de edición es **"referencia + bulk por embarque"**: el primer contenedor seleccionado conduce las etapas compartidas (BL, certificados, DUA, envío) y el cambio se replica a todos los seleccionados con estado optimista y revert por snapshot si el PATCH falla; los datos de unidad (nº/precinto/pesos/booking) se editan por contenedor.

Docs internas: [README](./documentos-proex-card/README.md) · [CLAUDE.md](./documentos-proex-card/CLAUDE.md) · [UI-DOCS.md](./documentos-proex-card/UI-DOCS.md) · [AGENTS.md](./documentos-proex-card/AGENTS.md)
(Nota: el README de la card está parcialmente desactualizado — describe una card sobre Deals con 3 certificados; la realidad es una card sobre Company con 3 tabs, incluida la Gestión integral.)

### `documentos-proex-microservice/` — Backend

FastAPI sobre Lambda que centraliza todas las operaciones con HubSpot para la fase de documentación. Cuatro routers registrados en `main.py`:

- **`documentos`** (`/api/v1/documentos`) — motor de pending / generate / rollback y precarga de contexto del deal (Tabs 1 y 2 de la card).
- **`documento_deal`** (`/api/v1/documento-deal`) — ciclo de vida del Negocio Documento: creación 1:1 vía webhook autenticado y recálculo monótono de dealstage.
- **`pedidos`** (`/api/v1/pedidos`) — capa de datos y edición del pedido para la Gestión (Tab 3): detalle, PATCH per-contenedor, subida/borrado de ficheros por embarque.
- **`empresas`** (`/api/v1/empresas`) — búsqueda de companies por nombre.

Render de PDF: overlay `reportlab` mergeado con `pypdf` sobre plantilla (`origen_borrador_plantilla.pdf`, `sanitario_plantilla.pdf`); el origen final se renderiza sobre A4 en blanco.

Docs internas: [CLAUDE.md](./documentos-proex-microservice/CLAUDE.md)
(No existe README.md ni DEPLOYMENT.md en el microservicio; el CLAUDE.md describe una propuesta original parcialmente desfasada respecto al código real.)

## 🔄 Flujos principales

1. **Alta del Negocio Documento (webhook, upstream Pedidos).** Un workflow de HubSpot dispara `POST /api/v1/documento-deal/webhooks/pedido-preparar-doc` cuando un Pedido entra en "Preparar Documentación". Con guard estricto (pipeline `725914649` + dealstage `1368383244`), idempotente y **saltando camión** (`tipo_contenedor` ∈ `{TRAILER80}` → estado `saltado_camion`), crea un deal en el pipeline `905179456` (etapa "En proceso"), replica la cabecera del pedido y clona las asociaciones a contenedor, cotización, company, elemento, cobro y proveedor. Invariante: **1 Negocio Documento : 1 Contenedor**.

2. **Generación de certificados (Tab 1).** Filtros empresa + tipos + fechas → `POST /pending` marca "pendiente" cada `doc_type` que esté en `documentos_a_generar` pero cuya propiedad de fichero esté vacía. El usuario selecciona contenedores del **mismo deal**, 1-3 tipos, idioma y descripción de mercancía (obligatoria para origen) → `POST /generate`: agrega productos/pesos, renderiza el PDF, lo sube al File Manager y persiste `file_id` + `doc_group_id_*` (mismo `group_generation_id` uuid) en **todos** los contenedores del grupo.

3. **Histórico y rollback (Tab 2).** `POST /generated` lista contenedores con ≥1 doc generado; `POST /rollback` localiza el grupo por `doc_group_id_*`, borra los ficheros del File Manager y limpia las props en todos los contenedores del grupo. En props multi-fichero (`certificado_origen`, `certificado_sanitario`) solo borra los ficheros cuyo nombre empieza por el prefijo del `doc_type` y conserva el resto.

4. **Gestión integral del embarque (Tab 3).** Selector empresa → pedido → `GET /pedidos/{numero}` (detalle + contenedores + `select_options`). Solo son gestionables los contenedores con `tiene_negocio_documento=true`. Edición por embarque: BL (`PATCH /pedidos/{numero}`), certificados validados (`.../contenedores/properties`), booking y datos físicos individuales (`.../contenedores/{cid}/booking|datos`), envío/recepción/waiver (`.../contenedores/{cid}/entrega`), y subida/borrado de ficheros por subconjunto de contenedores (Cambio 2). BL y booking se escriben en el Negocio Documento **y** en el Pedido-deal.

5. **Avance de dealstage (monótono).** Tras cada mutación de fichero/prop, el servicio recalcula best-effort el dealstage del Negocio Documento: **En proceso → Pte. confirmar → Confirmado → Enviada → Retirado**, derivando las señales de `documentos_a_generar` y las props de fichero. "Cierre perdido" es manual e intocable por el calculador.

6. **Puerta de envío al cliente.** `permitir_enviar_documentacion` controla todo el envío: mientras sea `false`, la etapa de recepción/retirada queda bloqueada. Administración puede aprobar aun con pago/documentos pendientes (confirmación en modal). Documento-first: BL, booking y flags se leen del Negocio Documento con fallback al Pedido.

## 🌐 API / Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/documentos/pending` | Contenedores con documentos pendientes (empresa + fechas + tipos) |
| POST | `/api/v1/documentos/generate` | Genera 1-3 PDFs para un grupo de contenedores del mismo deal |
| POST | `/api/v1/documentos/generated` | Contenedores con ≥1 documento generado (histórico) |
| POST | `/api/v1/documentos/rollback` | Borra fichero y limpia props del grupo de generación |
| GET | `/api/v1/documentos/deal-context/{deal_id}` | Precarga (idioma de preprints) |
| GET | `/api/v1/empresas?q=` | Búsqueda de companies por nombre (CONTAINS_TOKEN) |
| GET | `/api/v1/pedidos?company_id=` | Resumen de pedidos de la empresa |
| GET | `/api/v1/pedidos/{numero}?company_id=` | Detalle del pedido + contenedores + select_options |
| PATCH | `/api/v1/pedidos/{numero}` | BL por embarque (escribe Documento + Pedido) |
| PATCH | `/api/v1/pedidos/{numero}/contenedores/properties` | Flags de certificados validados |
| PATCH | `/api/v1/pedidos/{numero}/contenedores/{cid}/booking` | Booking individual por contenedor |
| PATCH | `/api/v1/pedidos/{numero}/contenedores/{cid}/datos` | Nº contenedor, precinto, pesos, tara |
| PATCH | `/api/v1/pedidos/{numero}/contenedores/{cid}/entrega` | Mensajería, recepción, retirada, waiver |
| POST | `/api/v1/pedidos/{numero}/files/upload?tipo_documento=&contenedor_ids=` | Subida multipart por embarque |
| GET | `/api/v1/pedidos/{numero}/files/upload-modal` | HTML iframe de subida (drag & drop) |
| DELETE | `/api/v1/pedidos/{numero}/files/{file_id}?tipo_documento=&contenedor_ids=` | Borrado simétrico por embarque |
| POST | `/api/v1/documento-deal/webhooks/pedido-preparar-doc` | Webhook (header `X-Webhook-Token`) → crea el Negocio Documento |
| POST | `/api/v1/documento-deal/sync/{pedido_deal_id}` | Re-disparo manual de la creación |
| GET | `/health` · `/` · `/docs` · `/redoc` | Health, welcome y OpenAPI |

## 🗃️ Modelo de datos (HubSpot)

- **Contenedor** (`2-54989406`) — **source of truth del estado de docs**. Props clave: `documentos_a_generar` (multi-select autoritativo), `certificado_origen_borrador`, `certificado_origen`, `certificado_sanitario`, `certificado_origen_validado`, `certificado_sanitario_validado`, `doc_group_id_origen_borrador` / `_origen_final` / `_sanitario`, `numero_contenedor`, `numero_precinto`, `peso_bruto`/`peso_neto`/`tara`, `etd`/`eta`, `tipo_contenedor`, `permitir_enviar_documentacion`, `documentacion_recibida`, `mercancia_retirada`, `waiver_validado`, `otros_documentos`, `fotos_de_carga`.
- **Elemento** (`2-54989407`) — líneas de mercancía del fabricante; agrega cajas/pesos y aporta `formato`/`marca`/`nombre_es|en|fr` a los certificados. Asociación Contenedor→Elemento typeId `491`.
- **Deal** en 3 roles clasificados por pipeline: **Cotización** (padre), **Pedido** (`725914649`), **Documento** (`905179456`). Props de deal que toca: `bl_validado_logistica`/`_administracion`, `bl_enviado_cliente`, `tipo_de_bl`, `borrador_bl` (borrador + final por prefijo de nombre), `numero_de_booking`, `certificado_origen_mercancia`, `factura_del_pedido`, `packing_list_proex`, `carta_de_porte_proex`, `numero_de_factura`, `fecha_de_vencimiento_factura`, `preprints_language`, `consignee`, `notify`, `shipper`, `puerto_salida`/`puerto_destino`, `almacen`.
- **Company** (`0-2`) — montaje de la card; `CrmDataHighlight` muestra `name`, `cif`, `tipo_cliente`, `residennum`, `phone`, `credito_concedido`.
- **Pipeline Documento** `905179456`: En proceso `1371580054` → Pte. confirmar `1371580055` → Confirmado `1371580056` → Enviada `1371580059` → Retirado `1380233754` (ganada); Cierre perdido `1371580060` (manual).
- **Asociaciones dedicadas del Negocio Documento:** documento→contenedor `682`, pedido→documento `681`, cotización→documento `684`; también clona company / elemento / cobro / proveedor.

## 🔌 Integraciones

- **Asistente Pedidos (upstream, webhook entrante):** el workflow del pipeline de Pedidos dispara `POST /documento-deal/webhooks/pedido-preparar-doc` al entrar en "Preparar Documentación". Autenticado por secreto compartido `X-Webhook-Token` vs `HUBSPOT_WEBHOOK_SECRET` (`hmac.compare_digest`); si el secreto falta, el webhook responde 503.
- **Asistente Cotizador (upstream, lectura):** las props de la cotización padre (consignee, notify, puertos, almacén, descripción de mercancía) se leen del deal y se replican al Negocio Documento.
- **Asistente Cobros (referencial):** la card enlaza al asistente de cobros para completar la asignación de importes por contenedor antes de permitir el envío; el % pendiente se calcula sobre contenedores con `price` informado.
- **SAP (indirecto, solo lectura):** el servicio lee `numero_de_factura` y `fecha_de_vencimiento_factura` que SAP escribe en el pedido-deal; nunca escribe hacia SAP.
- **HubSpot Files v3** (REST directo con `requests`): ficheros `PUBLIC_NOT_INDEXABLE`, `overwrite=False`, bajo `/documentos-proex/{bl,origen,sanitario,contenedor-docs,otros-documentos,fotos-carga}`; los IDs se serializan con `;` en las props.
- **HubSpot HubDB:** tabla `formato_producto` (traducción de formatos ES/EN/FR, cache en memoria con lock; lee la versión **publicada**, no el draft). La tabla de puertos para país destino del sanitario está declarada pero **no implementada** (`get_puerto_destination_country` lanza `NotImplementedError`; se usa el label de `Deal.puerto_destino`).
- **Sin colas/DLQ/S3:** servicio síncrono. El `.env` contiene variables `JOBS_*` vestigiales que la config ignora (`extra='ignore'`); no hay `deploy-worker.sh` ni `worker_handler.py`.

## 🚀 Despliegue

- **AWS Lambda** como imagen de contenedor (`public.ecr.aws/lambda/python:3.11`), región **eu-south-2**, cuenta `095235023391`, perfil AWS `biatic`. Función/repo ECR **`proex-documents`**, expuesta vía **API Gateway HTTP API** (no Function URL). Timeout 30 s, memoria 512 MB (el propio código sugiere subir a 1024 MB por `reportlab`+Pillow).
- **Handler:** `lambda_handler.handler = Mangum(app, lifespan="off")`.
- **`deploy.sh`** hace build `--platform linux/amd64 --no-cache`, push a ECR, crea/actualiza Lambda + rol IAM + policy ECR + API Gateway + permiso de invoke, y setea las variables de entorno. **No existe `deploy-worker.sh`** (servicio síncrono).
- **URL del API Gateway:** `https://2tqk2gn9n3.execute-api.eu-south-2.amazonaws.com` — hardcodeada en la card en **dos sitios que deben mantenerse sincronizados**: `config.js` (`API_CONFIG.baseURL`) y `app-hsmeta.json` (`permittedUrls.fetch`).
- **Variables de entorno destacadas:** `PROEX_ACCESS_TOKEN` (token HubSpot, REQUERIDO, debe empezar por `pat-` o `HUBSPOT_` — **no** `HUBSPOT_ACCESS_TOKEN` pese a lo que dice `.env.example`), `HUBSPOT_WEBHOOK_SECRET`, `CORS_ORIGINS`, `FILES_FOLDER` (`=/documentos-proex`), `SANITARIO_EMPRESA_DIRECCION`/`_ESTABLECIMIENTO`/`_JEFE_SALUD`/`_FIRMADO_EN` (textos fijos del certificado sanitario), `PDF_DEBUG_LAYOUT`.
- **Card:** despliegue como HubSpot Private App / UI Extension con HubSpot CLI (`hs project dev` / `build` / `upload` / `watch`); `hsproject.json` fija `srcDir=src`, platform version 2025.2. Sin `.env` (config estática).
- ⚠️ La infra AWS se aprovisionó **a mano** (no hay IaC) y los IDs de HubSpot están hardcodeados.

## 🧪 Testing

- **Microservicio:** `pytest 8.3.3` — 85 funciones de test en 15 ficheros bajo `tests/`, ejecutables con `pytest` desde la raíz del microservicio (`conftest.py` inserta el cwd en `sys.path`). Toda la red HubSpot se mockea con `monkeypatch`/`SimpleNamespace` (no toca HubSpot real). Cubre la lógica no trivial: creación 1:1 y guards del Negocio Documento, calculador de dealstage y derivación de flags, clasificación de deals por pipeline, Cambio 2 (subida/borrado por embarque), booking y datos de contenedor, agregación de certificados, formato/HubDB e idioma del sanitario, y auth del webhook. **No hay tests de render de PDF ni end-to-end HTTP.**
- **Card:** sin tests ni framework en el repo. El control de calidad es ESLint 9.37 (sin config versionada) y `npx tsc --noEmit`; la verificación real es manual con `hs project dev` (hot reload) sobre un sandbox.

## 📁 Estructura de carpetas

```
documentos/
├── documentos-proex-card/          # Card CRM (React / UI Extensions), montada en Company
│   └── src/app/cards/
│       ├── Documentos.jsx          # entrypoint: hubspot.extend → <Tabs> (Pendientes/Histórico/Gestión)
│       ├── config.js               # baseURL del microservicio + mapa de endpoints
│       ├── tabs/                   # DocumentosPendientesTab / DocumentosHistoricoTab / GestionDocumentacionTab
│       ├── components/             # FiltrosDocumentos, BLAccordion, CertificadoStepper, DetalleContenedorPanel, ...
│       ├── utils/                  # api.utils.js (fetchFromAPI), gestion.api.ts, documentos.utils.ts
│       └── constants/              # documentos.constants.ts (tipos doc, DOC_TYPE_TO_API, TipoPedido)
└── documentos-proex-microservice/  # Backend FastAPI + Mangum (Lambda, síncrono)
    ├── main.py                     # app FastAPI, CORS, registra 4 routers, /health y /
    ├── lambda_handler.py           # Mangum(app, lifespan="off")
    ├── deploy.sh · Dockerfile      # despliegue ECR + Lambda + API Gateway (perfil biatic)
    └── app/
        ├── core/                   # config.py (Settings) · constants.py (objectTypeIds, pipelines, TRANSLATIONS)
        ├── shared/                 # hubspot_client, hubspot_batch, files (Files v3), hubdb, elementos, properties
        ├── documentos/             # router + service (pending/generate/rollback), pdf_renderer, domain/{origen,sanitario}, templates/
        ├── documento_deal/         # router + service (creación 1:1), dealstage_calculator, webhook_auth
        ├── pedidos/                # router + service (detalle, PATCH per-contenedor, ficheros por embarque)
        └── empresas/               # router + service (search companies)
```

## 📚 Documentación relacionada

- Card: [README](./documentos-proex-card/README.md) · [CLAUDE.md](./documentos-proex-card/CLAUDE.md) · [UI-DOCS.md](./documentos-proex-card/UI-DOCS.md) · [AGENTS.md](./documentos-proex-card/AGENTS.md)
- Microservicio: [CLAUDE.md](./documentos-proex-microservice/CLAUDE.md)
- Global del repo: [HANDOVER-TECNICO-PROEX.md](../HANDOVER-TECNICO-PROEX.md) · [MODELO-DATOS-HUBSPOT-PROEX.md](../MODELO-DATOS-HUBSPOT-PROEX.md)
