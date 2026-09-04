// apps/web/src/app/page.tsx
'use client';

import { useCallback, useState } from 'react';
import { Header } from '../components/dashboard/Header';
import { TopologyCard } from '../components/dashboard/TopologyCard';
import { IncidentFeed } from '../components/dashboard/IncidentFeed';
import { AgentTerminal } from '../components/dashboard/AgentTerminal';
import { AuditLedgerModal } from '../components/dashboard/AuditLedgerModal';
import { ApprovalGateModal } from '../components/approval/ApprovalGateModal';
import { ConfigurationModal, type ConfigurationData } from '../components/dashboard/ConfigurationModal';
import { useIncidents } from '../hooks/useIncidents';
import { useTopology } from '../hooks/useTopology';
import { useAuditStatus } from '../hooks/useAuditStatus';
import { useWebSocketFeed } from '../hooks/useWebSocketFeed';
import { api } from '../lib/api';
import type { Incident } from '../types/incident';

export default function DashboardPage() {
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [showAuditModal, setShowAuditModal] = useState<boolean>(false);
  const [showConfiguration, setShowConfiguration] = useState<boolean>(true);
  const [configurationData, setConfigurationData] = useState<ConfigurationData | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Real data state hooks
  const { incidents, isLoading: isIncidentsLoading, refetch: refetchIncidents } = useIncidents();
  const { topology, refetch: refetchTopology } = useTopology();
  const { auditStatus, refetch: refetchAudit, triggerTamperTest } = useAuditStatus();

  // Reactive WebSocket telemetry feed
  const { connectionStatus, logs, clearLogs } = useWebSocketFeed({
    onIncidentEvent: useCallback(() => {
      refetchIncidents();
      refetchTopology();
      refetchAudit();
    }, [refetchIncidents, refetchTopology, refetchAudit]),
  });

  // Action: Trigger multi-archetype alert simulation
  const handleSimulateAlert = async (archetype?: string) => {
    setIsSimulating(true);
    try {
      await api.simulateAlert(archetype);
      await Promise.all([refetchIncidents(), refetchTopology(), refetchAudit()]);
    } catch (err: any) {
      console.error('Simulation error:', err.message);
    } finally {
      setIsSimulating(false);
    }
  };

  // Action: Add dynamic microservice node to topology
  const handleAddTopologyNode = async (node: {
    name: string;
    node_type: string;
    tier: string;
    connect_to?: string;
  }) => {
    await api.addTopologyNode(node);
    await refetchTopology();
  };

  // Action: Approve incident remediation patch
  const handleApprove = async (
    incidentId: string,
    signerId: string,
    signature: string,
    comments: string
  ) => {
    const updated = await api.approveIncident(incidentId, {
      signer_id: signerId,
      signature,
      comments,
    });
    setSelectedIncident(updated);
    await Promise.all([refetchIncidents(), refetchTopology(), refetchAudit()]);
  };

  // Action: Reject incident remediation patch
  const handleReject = async (
    incidentId: string,
    signerId: string,
    reason: string
  ) => {
    const updated = await api.rejectIncident(incidentId, {
      signer_id: signerId,
      reason,
    });
    setSelectedIncident(updated);
    await Promise.all([refetchIncidents(), refetchTopology(), refetchAudit()]);
  };

  const activeCount = incidents.filter(
    (i) => i.status === 'triaging' || i.status === 'patch_ready'
  ).length;

  return (
    <main className="dashboard-container">
      {showConfiguration && (
        <ConfigurationModal isOpen={showConfiguration} onComplete={async (data) => {
          try {
            await fetch('http://localhost:8000/config/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(data)
            });
          } catch (e) {
            console.error('Failed to save config', e);
          }
          setConfigurationData(data);
          setShowConfiguration(false);
        }} />
      )}
      {/* 1. Header with live status, WORM badge, and alert simulation */}
      <Header
        wsStatus={connectionStatus}
        auditStatus={auditStatus}
        activeCount={activeCount}
        onOpenAudit={() => setShowAuditModal(true)}
        onSimulate={handleSimulateAlert}
        isSimulating={isSimulating}
        onOpenConfig={() => setShowConfiguration(true)}
      />
      {/* LLM Status Badge */}
      <div style={{ padding: '0 20px', marginTop: '-10px', marginBottom: '10px', display: 'flex', gap: '8px' }}>
        {configurationData?.geminiKey ? (
          <span className="badge badge-resolved">LLM ACTIVE: {configurationData.geminiModel}</span>
        ) : (
          <span className="badge badge-warning">LLM INACTIVE: Rule-based Fallback</span>
        )}
        {configurationData?.slackWebhook && <span className="badge" style={{background: 'rgba(56, 189, 248, 0.1)'}}>Slack Connected</span>}
        {configurationData?.jiraToken && <span className="badge" style={{background: 'rgba(56, 189, 248, 0.1)'}}>Jira Connected</span>}
      </div>

      {/* 2. Main Two-Column Control Center Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 1fr)',
          gap: '20px',
        }}
      >
        {/* Left Column: Topology Knowledge Graph */}
        <TopologyCard
          topology={topology}
          selectedService={selectedService}
          onSelectService={setSelectedService}
          onAddNode={handleAddTopologyNode}
        />

        {/* Right Column: Incident Control Queue */}
        <IncidentFeed
          incidents={incidents}
          selectedService={selectedService}
          onSelectIncident={setSelectedIncident}
          isLoading={isIncidentsLoading}
        />
      </div>

      {/* 3. Bottom Full-Width Agent Reasoning & Sandbox Terminal */}
      <AgentTerminal logs={logs} onClearLogs={clearLogs} />

      {/* 4. WORM Cryptographic Audit Ledger Modal */}
      {showAuditModal && (
        <AuditLedgerModal
          auditStatus={auditStatus}
          onClose={() => setShowAuditModal(false)}
          onTamperTest={triggerTamperTest}
          onRefresh={refetchAudit}
        />
      )}

      {/* 5. Governance Approval Gate Modal */}
      {selectedIncident && (
        <ApprovalGateModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </main>
  );
}
