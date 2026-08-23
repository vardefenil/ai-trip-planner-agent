'use client';

import { PipelineStage } from '@/types/travel';

interface PipelineProgressProps {
  stages: PipelineStage[];
}

const STAGE_META: Record<string, { label: string; icon: string; color: string }> = {
  parsing:    { label: 'Parsing Request',    icon: '🔍', color: 'var(--teal)' },
  searching:  { label: 'Searching Options',  icon: '🌐', color: 'var(--lavender)' },
  ranking:    { label: 'Building Itinerary', icon: '🎯', color: 'var(--amber)' },
  presenting: { label: 'Finalising Packages',icon: '📦', color: 'var(--mint)' },
  booking:    { label: 'Booking Summary',    icon: '🎉', color: 'var(--coral)' },
};

export function PipelineProgress({ stages }: PipelineProgressProps) {
  return (
    <div className="pipeline-progress">
      {stages.map((stage, idx) => {
        const meta = STAGE_META[stage.id] ?? { label: stage.label, icon: stage.icon, color: 'var(--teal)' };
        const isLast = idx === stages.length - 1;

        return (
          <div key={stage.id} className="pipeline-step">
            {/* Indicator circle */}
            <div className={`step-indicator ${stage.status}`}>
              <span className="step-icon">
                {stage.status === 'running' ? (
                  <span className="spinner">⟳</span>
                ) : stage.status === 'done' ? (
                  '✓'
                ) : stage.status === 'error' ? (
                  '✗'
                ) : (
                  meta.icon
                )}
              </span>
            </div>

            {/* Connector line */}
            {!isLast && (
              <div
                className={`step-connector ${stage.status === 'done' ? 'done' : stage.status === 'running' ? 'running' : ''}`}
              />
            )}

            {/* Label */}
            <div className="step-label">
              <span className="step-name">{meta.label}</span>
              {stage.message && (
                <span className="step-message">{stage.message}</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
