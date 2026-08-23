'use client';

import { PipelineStage } from '@/types/travel';

interface PipelineProgressProps {
  stages: PipelineStage[];
}

const STAGE_CONFIG: Record<string, { label: string; icon: string }> = {
  parsing: { label: 'Parsing Request', icon: '🔍' },
  searching: { label: 'Searching Options', icon: '🌐' },
  ranking: { label: 'Building Itinerary', icon: '🎯' },
  presenting: { label: 'Preparing Packages', icon: '📦' },
  booking: { label: 'Booking Summary', icon: '🎉' },
};

export function PipelineProgress({ stages }: PipelineProgressProps) {
  return (
    <div className="pipeline-progress">
      {stages.map((stage, idx) => (
        <div key={stage.id} className="pipeline-step">
          <div className={`step-indicator ${stage.status}`}>
            <span className="step-icon">
              {stage.status === 'running' ? (
                <span className="spinner">⟳</span>
              ) : stage.status === 'done' ? (
                '✓'
              ) : stage.status === 'error' ? (
                '✗'
              ) : (
                stage.icon
              )}
            </span>
          </div>
          {idx < stages.length - 1 && (
            <div className={`step-connector ${stage.status === 'done' ? 'done' : ''}`} />
          )}
          <div className="step-label">
            <span className="step-name">{stage.label}</span>
            {stage.message && (
              <span className="step-message">{stage.message}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
