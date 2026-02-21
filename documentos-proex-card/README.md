# Documentos PROEX - HubSpot CRM Card 📄

> CRM Card para generación automática de certificados de contenedores (Origen y Sanitario)

![Status](https://img.shields.io/badge/status-active-success.svg)
![HubSpot](https://img.shields.io/badge/HubSpot-CRM_Card-ff7a59.svg)
![React](https://img.shields.io/badge/React-18.2.0-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3.3-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)

---

## 📋 Tabla de Contenido

- [Descripción General](#-descripción-general)
- [Tecnologías y Stack](#-tecnologías-y-stack)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Funcionalidades por Tab](#-funcionalidades-por-tab)
- [Scripts Disponibles](#-scripts-disponibles)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Desarrollo](#-desarrollo)
- [Deployment](#-deployment)

---

## 🎯 Descripción General

**Documentos PROEX** es una CRM Card personalizada para HubSpot que permite generar automáticamente certificados oficiales asociados a contenedores de exportación/importación directamente desde el Deal.

### ¿Qué hace el proyecto?

La extensión permite generar tres tipos de certificados oficiales:

1. **Certificado de Origen - Borrador**: Documento preliminar para revisión
2. **Certificado de Origen - Definitivo**: Documento oficial final
3. **Certificado Sanitario**: Certificado de cumplimiento sanitario

**Funcionalidades principales:**
- Selector de tipo de certificado
- Selección múltiple de contenedores asociados al Deal
- Generación automática de PDF desde plantillas
- Almacenamiento del archivo en propiedades file del Deal
- Regeneración permitida (sobrescribe archivo anterior)

### ¿Qué problema resuelve?

- **Generación manual de certificados**: Automatiza la creación de documentos oficiales desde plantillas
- **Dispersión de información**: Centraliza los certificados en el Deal correspondiente
- **Errores de transcripción**: Los datos se extraen directamente del CRM, eliminando errores manuales
- **Tiempo de procesamiento**: Reduce significativamente el tiempo de generación de documentación oficial
- **Trazabilidad**: Mantiene histórico de certificados generados en el Deal

### Para quién va dirigido

- **Equipo operativo de PROEX**: Personal que gestiona exportaciones y necesita generar certificados
- **Equipo comercial**: Para entregar documentación oficial a clientes
- **Administradores de HubSpot**: Configuran propiedades y permisos
- **Desarrolladores**: Mantienen y extienden la funcionalidad

### Contexto

Proyecto desarrollado para **PROEX** (empresa especializada en exportación/importación) como parte de su estrategia de digitalización y automatización de procesos comerciales en HubSpot CRM.

---

## 🛠️ Tecnologías y Stack

### Lenguajes
- **TypeScript 5.3.3** - Type safety en componentes React
- **JavaScript (JSX)** - Componentes React

### Frameworks y Librerías
- **React 18.2.0** - Biblioteca UI
- **HubSpot UI Extensions SDK** - Framework oficial de HubSpot para CRM Cards
  - `hubspot.fetch()` - HTTP client
  - `hubspot.crm.*` - APIs de CRM
  - UI Components propietarios (Button, Input, Table, etc.)

### Herramientas de desarrollo
- **ESLint 9.37.0** - Linting y code quality
- **Vite** - Build tool (integrado en HubSpot CLI)
- **HubSpot CLI** - Herramienta de desarrollo y deployment

### Integraciones
- **Documentos PROEX Microservice** - Backend API REST en FastAPI desplegado en AWS Lambda
- **HubSpot CRM API** - Lectura de deals, contacts, companies y line items
- **HubSpot File Manager API** - Subida y gestión de archivos PDF generados
- **Plantillas de documentos** - Templates DOCX/PDF para los 3 tipos de certificados

---

## 🏗️ Arquitectura

### Patrón de diseño

La extensión sigue el patrón **Component-Based Architecture** con gestión de estado local mediante React hooks:

```
┌──────────────────────────────────────────────────┐
│            HubSpot Deal (CRM)                    │
│  - Deal properties                               │
│  - Line Items (contenedores)                     │
│  - File properties (certificados generados)      │
└────────────────┬─────────────────────────────────┘
                 │
                 │ (1) Usuario abre Deal
                 ▼
┌────────────────────────────────────────────┐
│       Documentos CRM Card (React)          │
│  ┌──────────────────────────────────────┐ │
│  │ 1. Selector tipo certificado         │ │
│  │    - Origen Borrador                 │ │
│  │    - Origen Definitivo               │ │
│  │    - Sanitario                       │ │
│  ├──────────────────────────────────────┤ │
│  │ 2. Lista contenedores (checkboxes)   │ │
│  │    □ Contenedor A                    │ │
│  │    □ Contenedor B                    │ │
│  ├──────────────────────────────────────┤ │
│  │ 3. [Generar Certificado]             │ │
│  ├──────────────────────────────────────┤ │
│  │ 4. Link al PDF generado              │ │
│  └──────────────────────────────────────┘ │
└────────────────┬───────────────────────────┘
                 │
                 │ (2) POST /certificates/generate
                 ▼
┌────────────────────────────────────────────┐
│   FastAPI Microservice (AWS Lambda)        │
│  ┌──────────────────────────────────────┐ │
│  │ 1. Lee Deal + Contenedores (API)    │ │
│  │ 2. Selecciona plantilla              │ │
│  │ 3. Rellena datos en template         │ │
│  │ 4. Genera PDF                        │ │
│  │ 5. Sube a HubSpot File Manager       │ │
│  │ 6. Actualiza propiedad file del Deal │ │
│  └──────────────────────────────────────┘ │
└────────────────┬───────────────────────────┘
                 │
                 │ (3) Response + file URL
                 ▼
         [Archivo PDF guardado en Deal]
```

### Principios aplicados

- **Component Composition**: Componentes pequeños y reutilizables
- **Single Responsibility**: Cada componente gestiona una funcionalidad específica
- **Separation of Concerns**:
  - UI en componentes
  - Lógica de negocio en utils
  - Constantes separadas
  - Custom hooks para lógica reutilizable
- **DRY (Don't Repeat Yourself)**: Utilidades compartidas para API calls, validación, etc.
- **Optimización de Performance**: `useCallback`, `useMemo`, debouncing

### Flujo de datos

1. **Usuario abre Deal**: La CRM Card se carga automáticamente en el panel lateral
2. **Carga de contenedores**: Se obtienen los line items tipo "container" asociados al Deal
3. **Selección de tipo**: Usuario elige el tipo de certificado a generar
4. **Selección de contenedores**: Usuario marca uno o varios contenedores con checkboxes
5. **Generación**: Al hacer clic en "Generar Certificado":
   - Se envía solicitud al microservicio FastAPI
   - El backend lee los datos del Deal y contenedores desde HubSpot API
   - Se rellena la plantilla correspondiente con los datos
   - Se genera el PDF
   - Se sube al File Manager de HubSpot
   - Se actualiza la propiedad file del Deal
6. **Visualización**: El usuario ve el enlace al archivo generado y puede descargarlo
7. **Regeneración**: Si se vuelve a generar el mismo tipo de certificado, se sobrescribe el archivo anterior

---

## ✅ Requisitos Previos

### Software necesario

- **Node.js 18+** (recomendado 20 LTS)
- **npm** o **yarn**
- **HubSpot CLI**
  ```bash
  npm install -g @hubspot/cli
  ```

### Cuentas y accesos

- **Cuenta HubSpot** (Professional o Enterprise)
- **Private App Token** con permisos:
  - CRM Objects (read/write)
  - CRM Custom Objects (read/write)
  - HubDB (read)
- **Backend API URL** del microservicio FastAPI

### Propiedades del Deal requeridas

La extensión requiere las siguientes propiedades configuradas en Deals:

1. **certificado_origen_borrador** (type: file) - Almacena el PDF del Certificado de Origen Borrador
2. **certificado_origen_definitivo** (type: file) - Almacena el PDF del Certificado de Origen Definitivo
3. **certificado_sanitario** (type: file) - Almacena el PDF del Certificado Sanitario

### Line Items requeridos

- **Contenedores** - Line items de tipo "container" asociados al Deal

### Plantillas de documentos

El microservicio necesita acceso a las plantillas DOCX/PDF de los 3 certificados:
- `certificado_origen_borrador.docx`
- `certificado_origen_definitivo.docx`
- `certificado_sanitario.docx`

---

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd documentos-proex-card
```

### 2. Instalar HubSpot CLI

```bash
npm install -g @hubspot/cli
```

### 3. Autenticar con HubSpot

```bash
hs auth
```

Sigue las instrucciones para autenticarte con tu cuenta de HubSpot.

### 4. Instalar dependencias del proyecto

```bash
cd src/app/cards
npm install
```

---

## ⚙️ Configuración

### Configurar API endpoint del backend

Edita `src/app/cards/config.js`:

```javascript
const BACKEND_BASE_URL = "https://your-backend-api.com";

export { BACKEND_BASE_URL };
```

### Configurar hsproject.json

El archivo `hsproject.json` en la raíz define la configuración del proyecto:

```json
{
  "name": "documentos-proex-card",
  "srcDir": "src",
  "platformVersion": "2025.2"
}
```

### Configurar card metadata

Edita `src/app/cards/card-hsmeta.json` para configurar:
- Título de la card
- Descripciones
- Objeto CRM asociado (deals)

---

## 🚀 Uso

### Modo desarrollo local

```bash
# Desde el directorio raíz del proyecto
hs project dev
```

Esto iniciará:
- Servidor de desarrollo con hot reload
- Proxy para pruebas en HubSpot sandbox

### Acceder a la extensión

1. Ir a HubSpot CRM
2. Abrir cualquier Deal
3. La card "Documentos PROEX" aparecerá en el panel lateral

### Funcionalidades de la CRM Card

1. **Selector de tipo de certificado**
   - Dropdown con 3 opciones: Origen Borrador, Origen Definitivo, Sanitario

2. **Lista de contenedores del Deal**
   - Muestra todos los line items tipo "container"
   - Checkboxes para selección múltiple
   - Información básica de cada contenedor

3. **Generación de certificado**
   - Botón "Generar Certificado"
   - Validación de selecciones
   - Loading state durante generación
   - Mensaje de éxito/error

4. **Visualización del resultado**
   - Link al PDF generado
   - Posibilidad de regenerar (sobrescribe el anterior)
   - Descarga directa del archivo

---

## 🔧 Scripts Disponibles

### Desarrollo

```bash
# Iniciar servidor de desarrollo
hs project dev

# Compilar proyecto
hs project build

# Upload a HubSpot
hs project upload

# Modo watch (auto-upload en cambios)
hs project watch
```

### Testing y calidad de código

```bash
# Lint con ESLint
npm run lint

# Fix automático de issues de linting
npm run lint:fix

# Type checking (TypeScript)
npx tsc --noEmit
```

### Deployment

```bash
# Deploy completo a producción
hs project upload --account=production-account-id

# Deploy a sandbox
hs project upload --account=sandbox-account-id
```

---

## 📁 Estructura del Proyecto

```
documentos-proex-card/
│
├── hsproject.json                # Configuración del proyecto HubSpot
├── src/
│   └── app/
│       └── cards/
│           ├── Documentos.tsx           # Componente principal
│           ├── card-hsmeta.json         # Metadata de la card
│           ├── config.js                # Configuración (API URL)
│           ├── package.json
│           │
│           ├── utils/                   # Utilidades compartidas
│           │   ├── api.utils.js         # API calls centralizadas
│           │   └── validation.utils.js  # Validaciones
│           │
│           ├── hooks/                   # Custom React hooks
│           │   └── useDebounce.js       # Hook de debouncing
│           │
│           ├── constants/               # Constantes
│           │   ├── common.constants.js  # Constantes comunes
│           │   └── containers.constants.js # Constantes de contenedores
│           │
│           ├── types/                   # TypeScript types
│           │   └── common.types.ts      # Tipos comunes
│           │
│           └── dist/                    # Build output (generado)
│
├── CLAUDE.md                     # Documentación para Claude AI
├── UI-DOCS.md                    # Documentación de UI components
└── README.md                     # Este archivo
```

### Descripción de directorios críticos

- **`utils/`**: Funciones auxiliares reutilizables:
  - `api.utils.js`: Wrapper de `hubspot.fetch()` con manejo de errores
  - `validation.utils.js`: Funciones de validación de formularios

- **`hooks/`**: Custom React hooks:
  - `useDebounce.js`: Implementa debouncing para inputs

- **`constants/`**: Constantes compartidas (mensajes de error, configuraciones, etc.)

- **`types/`**: Definiciones de tipos TypeScript para type safety

---

## 💻 Desarrollo

### Arquitectura de componentes

Cada tab sigue este patrón:

```jsx
// TabName.jsx
import React, { useState, useEffect, useCallback } from "react";
import { hubspot } from "@hubspot/ui-extensions";
import { fetchFromAPI } from "../utils/api.utils";

const TabName = ({ dealId, onNext, onPrevious }) => {
  // 1. Estado local
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. Carga inicial
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetchFromAPI(`/deals/${dealId}/endpoint`);
        setData(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [dealId]);

  // 3. Handlers con useCallback
  const handleSave = useCallback(async () => {
    // Lógica de guardado
  }, [data, dealId]);

  // 4. Render
  return (
    <div>
      {/* UI */}
    </div>
  );
};

export default TabName;
```

### Best practices aplicadas

1. **Imports organizados**: React → UI components → Utils → Constants
2. **Performance**: `useCallback` y `useMemo` donde corresponda
3. **Error handling**: Try-catch en todas las API calls
4. **Loading states**: Feedback visual durante operaciones asíncronas
5. **Validación**: Antes de permitir navegación al siguiente tab
6. **JSDoc comments**: En funciones complejas
7. **Nombres descriptivos**: Variables y funciones auto-documentadas

### Debugging

Para debugging en HubSpot:

```javascript
// Console logs visibles en DevTools
console.log("[ClienteTab] Loading data...", data);

// Logs de errores
console.error("[ClienteTab] Error fetching data:", error);
```

### Testing local

1. Usar `hs project dev` para hot reload
2. Probar en un deal de sandbox
3. Verificar Network tab para API calls
4. Revisar Console para errores

---

## 🚢 Deployment

### Pre-deployment checklist

- [ ] Tests pasados
- [ ] Linting sin errores
- [ ] Configuración de producción en `config.js`
- [ ] Backend API en producción funcionando
- [ ] Custom objects configurados en HubSpot
- [ ] HubDB tables pobladas

### Deploy a producción

```bash
# 1. Build del proyecto
hs project build

# 2. Upload a cuenta de producción
hs project upload --account=production-account-id

# 3. Verificar en HubSpot UI
```

### Rollback

Si algo falla:

```bash
# Revertir a versión anterior
hs project upload --account=production-account-id --version=previous
```

---

## 🎨 UI Components de HubSpot

La extensión utiliza los componentes oficiales de HubSpot UI Extensions:

- `Button` - Botones de acción
- `Input` - Campos de texto
- `Select` - Dropdowns
- `Table` - Tablas de datos
- `Flex` - Layout flexbox
- `Text` - Tipografía
- `Divider` - Separadores
- `Alert` - Mensajes de error/éxito
- `LoadingSpinner` - Indicadores de carga
- `Modal` - Ventanas modales (futuro)

Ver [UI-DOCS.md](./UI-DOCS.md) para documentación completa de componentes.

---

## 📝 Notas adicionales

### Limitaciones conocidas

1. **Rate limiting**: HubSpot API tiene límites de 100 calls/10 segundos
2. **Tamaño de payload**: Máximo 10MB por request
3. **Timeout**: Requests mayores a 30s pueden fallar
4. **Navegador**: Requiere navegadores modernos (Chrome, Firefox, Safari)

### Roadmap

- [x] Certificado de Origen - Borrador
- [x] Certificado de Origen - Definitivo
- [x] Certificado Sanitario
- [ ] Historial de certificados generados con versiones
- [ ] Envío automático por email al cliente
- [ ] Firma digital de certificados
- [ ] Integración con API de cámaras de comercio

---

## 🤝 Contribución

### Flujo de desarrollo

1. Crear rama desde `main`: `git checkout -b feature/nueva-funcionalidad`
2. Desarrollar y commitear cambios
3. Hacer push y crear Pull Request
4. Code review
5. Merge a `main`
6. Deploy automático

### Convenciones de código

- Usar ESLint configuration del proyecto
- Nombres de variables en camelCase
- Nombres de componentes en PascalCase
- Comentarios JSDoc en funciones públicas
- Commits descriptivos en inglés

---

## 📄 Licencia

Proyecto privado - PROEX

---

## 📞 Contacto y soporte

Para preguntas, reportar bugs o solicitar features:

- **Equipo de desarrollo PROEX**
- **Documentación interna**: Ver `CLAUDE.md` y `UI-DOCS.md`

---

**Versión**: 1.0.0
**Última actualización**: Noviembre 2024
**Platform Version**: HubSpot 2025.2
