'use client';

import { useState, useEffect } from 'react';
import { Settings, Cpu, Link as LinkIcon, Database, Check } from 'lucide-react';

export interface ConfigurationData {
  repoUrl: string;
  githubToken: string;
  useSandbox: boolean;
  geminiKey: string;
  geminiModel: string;
  slackWebhook: string;
  jiraToken: string;
  awsAccessKey: string;
}

interface ConfigurationModalProps {
  onComplete: (data: ConfigurationData) => void;
  isOpen: boolean;
}

export function ConfigurationModal({ onComplete, isOpen }: ConfigurationModalProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'ai' | 'integrations'>('general');
  const [models, setModels] = useState<{name: string, displayName: string, description: string}[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  
  const [data, setData] = useState<ConfigurationData>({
    repoUrl: 'https://github.com/23f2001317/vehicle-parking-v2.git',
    githubToken: '',
    useSandbox: true,
    geminiKey: '',
    geminiModel: 'gemini-1.5-pro',
    slackWebhook: '',
    jiraToken: '',
    awsAccessKey: ''
  });

  // Fetch models when API key is entered
  useEffect(() => {
    if (data.geminiKey.length > 20) {
      let defaultModel = data.geminiModel;
      const key = data.geminiKey;
      if (key.startsWith('AIza')) {
        defaultModel = '3.5 FLASH';
      } else if (key.startsWith('sk-proj') || key.startsWith('sk-')) {
        defaultModel = '5.4';
      } else if (key.startsWith('sk-ant') || key.startsWith('ant-')) {
        defaultModel = 'CLAUDE OPUS 4.6';
      }
      
      setData(d => d.geminiModel === defaultModel ? d : { ...d, geminiModel: defaultModel });
      setLoadingModels(true);
      fetch('http://localhost:8000/config/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey: data.geminiKey })
      })
      .then(res => res.json())
      .then(resData => {
        if (resData.status === 'success' && resData.models.length > 0) {
          setModels(resData.models);
          // Auto select first model if current is not in list
          if (!resData.models.find((m: any) => m.name === defaultModel)) {
             setData(d => ({...d, geminiModel: resData.models[0].name}));
          }
        }
      })
      .finally(() => setLoadingModels(false));
    }
  }, [data.geminiKey]);

  if (!isOpen) return null;

  const handleSave = () => {
    onComplete(data);
  };

  const tabs = [
    { id: 'general', label: 'General', icon: <Database size={14} /> },
    { id: 'ai', label: 'AI Intelligence', icon: <Cpu size={14} /> },
    { id: 'integrations', label: 'Integrations', icon: <LinkIcon size={14} /> },
  ] as const;

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{ maxWidth: '700px', padding: '0' }}>
        
        {/* Header */}
        <div style={{ padding: '24px 24px 0 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <Settings className="text-primary" size={24} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Kautilya AI Control Center
            </h3>
          </div>
          
          {/* Tabs */}
          <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === tab.id ? '2px solid var(--color-primary)' : '2px solid transparent',
                  color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  fontWeight: 500,
                  fontSize: '0.9rem',
                  transition: 'all 0.2s ease'
                }}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: '24px', minHeight: '350px' }}>
          
          {/* General Tab */}
          {activeTab === 'general' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Target Repository URL</label>
                <input
                  type="text"
                  value={data.repoUrl}
                  onChange={(e) => setData({ ...data, repoUrl: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                  placeholder="https://github.com/..."
                />
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>Kautilya AI will autonomously scan this repository and build a topology graph.</p>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>GitHub PAT (Scoped to repo)</label>
                <input
                  type="password"
                  value={data.githubToken}
                  onChange={(e) => setData({ ...data, githubToken: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                  placeholder="ghp_..."
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <input
                  type="checkbox"
                  checked={data.useSandbox}
                  onChange={(e) => setData({ ...data, useSandbox: e.target.checked })}
                  id="sandbox-toggle"
                  style={{ width: '18px', height: '18px', marginTop: '2px' }}
                />
                <div>
                  <label htmlFor="sandbox-toggle" style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)', cursor: 'pointer' }}>
                    Enable Autonomous Execution Sandbox
                  </label>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '4px 0 0 0', lineHeight: 1.4 }}>
                    If enabled, Kautilya AI will run patches in an isolated environment before submitting pull requests. Required for full autonomous mode.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* AI Tab */}
          {activeTab === 'ai' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Google Gemini API Key</label>
                <input
                  type="password"
                  value={data.geminiKey}
                  onChange={(e) => setData({ ...data, geminiKey: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                  placeholder="AIzaSy..."
                />
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Model Selection {loadingModels && <span style={{ color: 'var(--color-primary)', fontSize: '0.75rem', marginLeft: '8px' }}>Fetching models...</span>}
                </label>
                <select
                  value={data.geminiModel}
                  onChange={(e) => setData({ ...data, geminiModel: e.target.value })}
                  disabled={models.length === 0}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                >
                  {models.length === 0 && <option value={data.geminiModel}>{data.geminiModel} (Default)</option>}
                  {models.map(m => (
                    <option key={m.name} value={m.name} style={{background: '#1a1a2e'}}>{m.displayName} ({m.name})</option>
                  ))}
                </select>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>Select the preferred AI model for the Agent Orchestrator.</p>
              </div>
            </div>
          )}

          {/* Integrations Tab */}
          {activeTab === 'integrations' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '4px', marginTop: 0 }}>
                Connect third-party systems to allow Kautilya AI to autonomously triage and remediate alerts.
              </p>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Slack Webhook URL</label>
                <input
                  type="password"
                  value={data.slackWebhook}
                  onChange={(e) => setData({ ...data, slackWebhook: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                  placeholder="https://hooks.slack.com/services/..."
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Jira API Token</label>
                <input
                  type="password"
                  value={data.jiraToken}
                  onChange={(e) => setData({ ...data, jiraToken: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                  placeholder="ATATT3xFfGF0..."
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>AWS Access Key</label>
                <input
                  type="password"
                  value={data.awsAccessKey}
                  onChange={(e) => setData({ ...data, awsAccessKey: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff', fontSize: '0.9rem' }}
                  placeholder="AKIA..."
                />
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div style={{ padding: '20px 24px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'flex-end', background: 'var(--bg-subtle)', borderBottomLeftRadius: '12px', borderBottomRightRadius: '12px' }}>
          <button type="button" onClick={handleSave} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Check size={16} /> Save Configuration & Initialize
          </button>
        </div>
      </div>
    </div>
  );
}
