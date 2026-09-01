import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';

interface LogLine {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  message: string;
}

export const MetricsDashboard: React.FC = () => {
  const [logs, setLogs] = useState<LogLine[]>([
    { timestamp: "09:40:02", level: "INFO", message: "ClusterFlow Daemon initialized successfully on worker nodes" },
    { timestamp: "09:40:15", level: "INFO", message: "Database handshake verified on clusterflow_db collection" },
    { timestamp: "09:41:22", level: "INFO", message: "Scheduler matching cycle completed in 1.45ms, 0 pending tasks" },
    { timestamp: "09:42:01", level: "WARN", message: "Worker node agent-04 resource utilization crossed 85% cpu threshold" },
  ]);

  useEffect(() => {
    const messages = [
      "Job ML-Training-ResNet successfully assigned to worker agent-02",
      "WebSocket handshake completed for user operator@clusterflow.io",
      "Garbage collection executed, cleaned 4 completed jobs from memory Cache",
      "Heartbeat ping verified for active worker agent-03",
    ];

    const timer = setInterval(() => {
      const randomMsg = messages[Math.floor(Math.random() * messages.length)];
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      
      setLogs((prev) => [
        ...prev.slice(-9), // Keep last 10 logs
        { timestamp: timeStr, level: "INFO", message: randomMsg }
      ]);
    }, 4000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="text-center py-6">
            <h5 className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-2">Metrics Endpoint</h5>
            <a href="http://localhost:9090/metrics" target="_blank" rel="noreferrer" className="text-sm font-semibold text-primary hover:text-primary underline font-mono">
              /metrics (:9090)
            </a>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="text-center py-6">
            <h5 className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-2">Avg Sched Latency</h5>
            <p className="text-2xl font-bold text-cyan-600 font-mono">1.84 ms</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="text-center py-6">
            <h5 className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-2">Cluster Throughput</h5>
            <p className="text-2xl font-bold text-emerald-600 font-mono">12.5 jobs/m</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="text-center py-6">
            <h5 className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-2">Queue Buffer Load</h5>
            <p className="text-2xl font-bold text-purple-400 font-mono">0.02%</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="h-2 w-2 bg-emerald-500 rounded-full animate-ping" />
            Cluster Server Live Terminal Logs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-background border border-border rounded-md p-4 font-mono text-xs overflow-y-auto h-64 space-y-2 select-text">
            {logs.map((log, idx) => (
              <div key={idx} className="flex gap-2">
                <span className="text-muted-foreground">[{log.timestamp}]</span>
                <span className={log.level === 'ERROR' ? 'text-destructive' : log.level === 'WARN' ? 'text-yellow-500' : 'text-primary'}>
                  {log.level}
                </span>
                <span className="text-muted-foreground">{log.message}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
