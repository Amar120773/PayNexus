import React from 'react';
import { WorkerNode } from '../../../types';
import { StatusBadge } from '../../../components/ui/StatusBadge';

interface WorkerCardProps {
  worker: WorkerNode;
}

export const WorkerCard: React.FC<WorkerCardProps> = ({ worker }) => {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = 2;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const getLoadColor = (pct: number) => {
    if (pct > 80) return 'bg-red-500';
    if (pct > 50) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  const memoryPercent = worker.resources.totalMemoryBytes > 0 
    ? (worker.resources.usedMemoryBytes / worker.resources.totalMemoryBytes) * 100 
    : 0;

  return (
    <div className="bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 p-6 space-y-4 hover:border-primary/20 transition-all flex flex-col justify-between">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground font-mono">{worker.id}</h4>
          <StatusBadge status={worker.state} />
        </div>
        <p className="text-muted-foreground text-xs font-mono">{worker.hostname} ({worker.ipAddress})</p>
      </div>

      <div className="space-y-3 pt-2">
        <div className="space-y-1">
          <div className="flex justify-between text-xs font-mono text-muted-foreground">
            <span>CPU Core Loads ({worker.resources.cpuCores} Cores)</span>
            <span>{worker.resources.cpuUsagePercent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
            <div 
              className={`h-full ${getLoadColor(worker.resources.cpuUsagePercent)}`} 
              style={{ width: `${worker.resources.cpuUsagePercent}%` }}
            />
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-xs font-mono text-muted-foreground">
            <span>Memory Pool</span>
            <span>{memoryPercent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
            <div 
              className={`h-full ${getLoadColor(memoryPercent)}`} 
              style={{ width: `${memoryPercent}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
            <span>Used: {formatBytes(worker.resources.usedMemoryBytes)}</span>
            <span>Total: {formatBytes(worker.resources.totalMemoryBytes)}</span>
          </div>
        </div>
      </div>

      <div className="pt-2 border-t border-border flex justify-between items-center text-[10px] font-mono text-muted-foreground">
        <span>Heartbeat: {new Date(worker.lastHeartbeat).toLocaleTimeString()}</span>
        <span className="bg-muted border border-border text-primary font-bold px-2 py-0.5 rounded">
          {worker.runningTasks?.length || 0} Tasks running
        </span>
      </div>
    </div>
  );
};
