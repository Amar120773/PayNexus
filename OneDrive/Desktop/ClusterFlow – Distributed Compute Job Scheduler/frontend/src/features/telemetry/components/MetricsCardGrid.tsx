import React from 'react';
import { Card, CardContent } from '../../../components/ui/Card';

interface MetricsGridProps {
  stats: {
    workers: { online: number; total: number };
    resources: { avgCpuLoad: number; totalMemoryBytes: number; usedMemoryBytes: number };
    jobs: { pending: number; running: number; succeeded: number; failed: number };
  };
  throughput?: number;
}

export const MetricsCardGrid: React.FC<MetricsGridProps> = ({ stats, throughput = 0 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card>
        <CardContent className="flex items-center gap-4 py-4 select-text">
          <div className="p-4 rounded-lg bg-primary/10 text-primary text-3xl font-bold font-mono">
            {stats.workers.online}
          </div>
          <div>
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Nodes Online</h5>
            <p className="text-muted-foreground text-xs mt-1">Total Cluster size: {stats.workers.total}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-4 py-4 select-text">
          <div className="p-4 rounded-lg bg-primary/10 text-primary text-3xl font-bold font-mono">
            {stats.jobs.running}
          </div>
          <div>
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Tasks</h5>
            <p className="text-muted-foreground text-xs mt-1">{stats.jobs.pending} queued buffer jobs</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-4 py-4 select-text">
          <div className="p-4 rounded-lg bg-emerald-500/10 text-emerald-600 text-3xl font-bold font-mono">
            {throughput.toFixed(1)}
          </div>
          <div>
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Throughput</h5>
            <p className="text-muted-foreground text-xs mt-1">Jobs processed / min</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-4 py-4 select-text">
          <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-3xl font-bold font-mono">
            {stats.jobs.failed}
          </div>
          <div>
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Task Crashes</h5>
            <p className="text-muted-foreground text-xs mt-1">Total failed executions</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
