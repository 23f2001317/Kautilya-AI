// apps/web/src/components/dashboard/OnboardingModal.tsx
'use client';

import { useState } from 'react';

export interface OnboardingData {
  repoUrl: string;
  githubToken: string;
  useSandbox: boolean;
  geminiKey: string;
}

interface OnboardingModalProps {
  onComplete: (data: OnboardingData) => void;
}

export function OnboardingModal({ onComplete }: OnboardingModalProps) {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OnboardingData>({
    repoUrl: 'https://github.com/23f2001317/vehicle-parking-v2.git',
    githubToken: '',
    useSandbox: true,
    geminiKey: '',
  });

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    else onComplete(data);
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{ maxWidth: '600px' }}>
        <div className="modal-header">
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
            Kautilya AI - Environment Setup (Step {step}/3)
          </h3>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {step === 1 && (
            <>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Configure the target repository for Kautilya AI to monitor and remediate.
              </p>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#e2e8f0', marginBottom: '8px' }}>Target Repository URL</label>
                <input
                  type="text"
                  value={data.repoUrl}
                  onChange={(e) => setData({ ...data, repoUrl: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff' }}
                  placeholder="https://github.com/..."
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#e2e8f0', marginBottom: '8px' }}>GitHub PAT (Scoped to repo)</label>
                <input
                  type="password"
                  value={data.githubToken}
                  onChange={(e) => setData({ ...data, githubToken: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff' }}
                  placeholder="ghp_..."
                />
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Configure the execution sandbox for verifiable remediation.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <input
                  type="checkbox"
                  checked={data.useSandbox}
                  onChange={(e) => setData({ ...data, useSandbox: e.target.checked })}
                  id="sandbox-toggle"
                  style={{ width: '18px', height: '18px' }}
                />
                <label htmlFor="sandbox-toggle" style={{ fontSize: '0.9rem', color: '#e2e8f0', cursor: 'pointer' }}>
                  Enable Ephemeral Sandbox Execution
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Runs patches in an isolated environment before approval.
                  </div>
                </label>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Provide intelligence layer credentials (Gemini).
              </p>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#e2e8f0', marginBottom: '8px' }}>Gemini API Key</label>
                <input
                  type="password"
                  value={data.geminiKey}
                  onChange={(e) => setData({ ...data, geminiKey: e.target.value })}
                  style={{ width: '100%', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: '#fff' }}
                  placeholder="AIzaSy..."
                />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                  If left blank, Kautilya AI will degrade to heuristic rule-based mode.
                </div>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
          {step > 1 ? (
            <button onClick={() => setStep(step - 1)} className="btn btn-outline" style={{ fontSize: '0.8rem' }}>
              Back
            </button>
          ) : (
            <div></div>
          )}
          <button onClick={handleNext} className="btn btn-primary" style={{ fontSize: '0.8rem' }}>
            {step === 3 ? 'Launch Kautilya AI' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
