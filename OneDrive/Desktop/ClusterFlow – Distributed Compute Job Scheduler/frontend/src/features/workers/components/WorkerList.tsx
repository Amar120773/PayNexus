import React from 'react';
import { WorkerNode } from '../../../types';

interface WorkerListProps {
  workers: WorkerNode[];
}

export const WorkerList: React.FC<WorkerListProps> = ({ workers }) => {
  const getStatusColor = (state: string) => {
    switch (state) {
      case 'ACTIVE': return 'bg-emerald-500/20 text-emerald-600 border border-emerald-500/30 pulse-success';
      case 'IDLE': return 'bg-cyan-500/20 text-cyan-600 border border-cyan-500/30';
      case 'MAINTENANCE': return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
      case 'OFFLINE': return 'bg-slate-500/20 text-muted-foreground border border-slate-500/20';
      default: return 'bg-slate-700/20 text-muted-foreground';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (workers.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground border border-border rounded-lg bg-background/20">
        No active compute agents are registered in the cluster pool.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-left border-collapse bg-background/20">
        <thead>
          <tr className="border-b border-border text-xs text-muted-foreground font-semibold uppercase tracking-wider bg-muted">
            <th className="py-4 px-6">Compute Node Info</th>
            <th className="py-4 px-6">IP Address</th>
            <th className="py-4 px-6">Status</th>
            <th className="py-4 px-6">CPU utilization</th>
            <th className="py-4 px-6">Memory consumption</th>
            <th className="py-4 px-6">Active Tasks</th>
            <th className="py-4 px-6">Last Ping</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 text-sm text-muted-foreground">
          {workers.map((node) => {
            const memPercent = node.resources.totalMemoryBytes 
              ? (node.resources.usedMemoryBytes / node.resources.totalMemoryBytes) * 100 
              : 0;

            return (
              <tr key={node.id} className="hover:bg-white/5 transition-colors">
                <td className="py-4 px-6">
                  <div className="font-semibold text-muted-foreground">{node.hostname}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{node.id}</div>
                </td>
                <td className="py-4 px-6 font-mono text-xs text-muted-foreground">
                  {node.ipAddress}
                </td>
                <td className="py-4 px-6">
                  <span className={`px-2.5 py-1 rounded text-xs font-semibold ${getStatusColor(node.state)}`}>
                    {node.state}
                  </span>
                </td>
                <td className="py-4 px-6">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground w-10 font-mono">{node.resources.cpuUsagePercent.toFixed(1)}%</span>
                    <div className="h-1.5 w-24 bg-muted rounded-full overflow-hidden border border-border">
                      <div 
                        className={`h-full ${node.resources.cpuUsagePercent > 80 ? 'bg-red-500' : 'bg-indigo-500'}`} 
                        style={{ width: `${node.resources.cpuUsagePercent}%` }} 
                      />
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">({node.resources.cpuCores} cores)</span>
                  </div>
                </td>
                <td className="py-4 px-6">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground w-10 font-mono">{memPercent.toFixed(1)}%</span>
                    <div className="h-1.5 w-24 bg-muted rounded-full overflow-hidden border border-border">
                      <div 
                        className={`h-full ${memPercent > 80 ? 'bg-red-500' : 'bg-cyan-400'}`} 
                        style={{ width: `${memPercent}%` }} 
                      />
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">({formatBytes(node.resources.totalMemoryBytes)})</span>
                  </div>
                </td>
                <td className="py-4 px-6 text-center">
                  <span className="text-muted-foreground font-semibold">{node.runningTasks.length}</span>
                </td>
                <td className="py-4 px-6 text-muted-foreground text-xs font-mono">
                  {new Date(node.lastHeartbeat).toLocaleTimeString()}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
