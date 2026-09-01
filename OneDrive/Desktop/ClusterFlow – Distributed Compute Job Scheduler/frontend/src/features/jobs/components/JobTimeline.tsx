import React from 'react';
import { Task } from '../../../types';
import { StatusBadge } from '../../../components/ui/StatusBadge';

interface JobTimelineProps {
  tasks: Task[];
}

export const JobTimeline: React.FC<JobTimelineProps> = ({ tasks }) => {
  if (tasks.length === 0) return null;

  return (
    <div className="relative border-l border-border ml-3 pl-6 space-y-6">
      {tasks.map((task, idx) => {
        const start = task.startedAt ? new Date(task.startedAt).toLocaleTimeString() : '-';
        const finish = task.finishedAt ? new Date(task.finishedAt).toLocaleTimeString() : '-';

        return (
          <div key={task.id || idx} className="relative">
            <span className={`absolute -left-[31px] top-1.5 h-3.5 w-3.5 rounded-full border-2 bg-background ${
              task.state === 'SUCCEEDED' ? 'border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]' :
              task.state === 'FAILED' ? 'border-red-500 shadow-[0_0_8px_rgba(239,68,68,0.3)]' :
              task.state === 'RUNNING' ? 'border-blue-500 animate-pulse' : 'border-input'
            }`} />

            <div className="bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 p-4 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="text-xs font-mono font-bold text-muted-foreground">TASK: </span>
                  <span className="text-xs font-semibold text-foreground font-mono">{task.id}</span>
                </div>
                <StatusBadge status={task.state} />
              </div>

              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground font-mono">
                <div>Node: <span className="text-primary">{task.assignedNode || 'Unassigned'}</span></div>
                <div>Exit Code: <span className={task.exitCode !== 0 ? 'text-destructive font-bold' : 'text-muted-foreground'}>{task.exitCode}</span></div>
                <div>Start: <span className="text-muted-foreground">{start}</span></div>
                <div>Finish: <span className="text-muted-foreground">{finish}</span></div>
              </div>

              {task.errorLog && (
                <div className="mt-2 bg-red-500/5 border border-red-500/10 rounded p-2 text-[10px] font-mono text-red-300 select-text overflow-x-auto">
                  {task.errorLog}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
