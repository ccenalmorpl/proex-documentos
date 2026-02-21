// React core
import React, { useState } from "react";

// HubSpot UI Extensions
import { Tabs, Tab } from "@hubspot/ui-extensions";
import { hubspot } from "@hubspot/ui-extensions";

// Tabs
import DocumentosPendientesTab from "./tabs/DocumentosPendientesTab";
import DocumentosHistoricoTab from "./tabs/DocumentosHistoricoTab";

// Constants
import { TAB_PENDIENTES, TAB_HISTORICO } from "./constants/documentos.constants";

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
      <Tab tabId={TAB_PENDIENTES} title="Generar documentos">
        <DocumentosPendientesTab context={context} actions={actions} />
      </Tab>

      <Tab tabId={TAB_HISTORICO} title="Histórico / Rollback">
        <DocumentosHistoricoTab context={context} actions={actions} />
      </Tab>
    </Tabs>
  );
};
