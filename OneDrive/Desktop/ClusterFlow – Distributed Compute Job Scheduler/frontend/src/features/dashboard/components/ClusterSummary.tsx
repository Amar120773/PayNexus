import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '../../../components/ui/Card';
import { useWebSocket } from '../../../context/WebSocketContext';

interface ClusterStats {
  activeNodes: number;
  totalCores: number;
  totalMemoryGb: number;
  jobsPending: number;
  jobsRunning: number;
  jobsSucceeded: number;
}

export const ClusterSummary: React.FC = () => {
  const { subscribe } = useWebSocket();
  const [stats, setStats] = useState<ClusterStats>({
    activeNodes: 4,
    totalCores: 64,
    totalMemoryGb: 256,
    jobsPending: 12,
    jobsRunning: 3,
    jobsSucceeded: 142,
  });

  useEffect(() => {
    // Listen to statistics event sent by the WebSocket gateway
    const unsubscribe = subscribe('stats_summary', (payload: ClusterStats) => {
      setStats(payload);
    });
    return () => unsubscribe();
  }, [subscribe]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <Card>
        <CardContent className="flex items-center gap-4 py-2">
          <div className="p-4 rounded-lg bg-primary/10 text-primary text-3xl font-bold">
            {stats.activeNodes}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Cluster Compute Nodes</h4>
            <p className="text-muted-foreground text-sm mt-1">{stats.totalCores} vCPUs / {stats.totalMemoryGb} GB RAM</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-4 py-2">
          <div className="p-4 rounded-lg bg-cyan-500/10 text-cyan-600 text-3xl font-bold">
            {stats.jobsRunning}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Execution</h4>
            <p className="text-muted-foreground text-sm mt-1">{stats.jobsPending} jobs waiting in queue</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-4 py-2">
          <div className="p-4 rounded-lg bg-emerald-500/10 text-emerald-600 text-3xl font-bold">
            {stats.jobsSucceeded}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Completed Jobs</h4>
            <p className="text-muted-foreground text-sm mt-1">Success rate: 98.4%</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
