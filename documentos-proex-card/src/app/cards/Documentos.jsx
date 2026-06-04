import React, { useState } from "react";

import { Tabs, Tab } from "@hubspot/ui-extensions";
import { hubspot } from "@hubspot/ui-extensions";

import DocumentosPendientesTab from "./tabs/DocumentosPendientesTab";
import DocumentosHistoricoTab from "./tabs/DocumentosHistoricoTab";
import GestionDocumentacionTab from "./tabs/GestionDocumentacionTab";

import { TAB_PENDIENTES, TAB_HISTORICO, TAB_GESTION } from "./constants/documentos.constants";

hubspot.extend(({ context, actions }) => (
  <DocumentosCard context={context} actions={actions} />
));

const DocumentosCard = ({ context, actions }) => {
  const [selectedTab, setSelectedTab] = useState(TAB_PENDIENTES);

  return (
    <Tabs
      variant="enclosed"
      selected={selectedTab}
      onSelectedChange={setSelectedTab}
    >
      <Tab tabId={TAB_PENDIENTES} title="Generar certificados">
        <DocumentosPendientesTab context={context} actions={actions} />
      </Tab>

      <Tab tabId={TAB_HISTORICO} title="Histórico de certificados">
        <DocumentosHistoricoTab context={context} actions={actions} />
      </Tab>

      <Tab tabId={TAB_GESTION} title="Gestión de documentación">
        <GestionDocumentacionTab context={context} actions={actions} />
      </Tab>
    </Tabs>
  );
};
