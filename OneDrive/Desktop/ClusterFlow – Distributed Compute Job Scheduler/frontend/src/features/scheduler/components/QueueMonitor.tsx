import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

interface QueueTaskItem {
  id: string;
  jobName: string;
  priority: number;
  cores: number;
  memoryMb: number;
  queuedTime: string;
}

export const QueueMonitor: React.FC = () => {
  const [algo, setAlgo] = useState<'FIFO' | 'FAIR' | 'PRIORITY'>('PRIORITY');
  
  // Mock data representing the scheduler queue items
  const queueItems: QueueTaskItem[] = [
    { id: "task-102", jobName: "ML-Training-ResNet", priority: 10, cores: 16, memoryMb: 65536, queuedTime: "12s ago" },
    { id: "task-103", jobName: "Data-Ingest-S3", priority: 8, cores: 8, memoryMb: 32768, queuedTime: "34s ago" },
    { id: "task-104", jobName: "Analytics-Report-Monthly", priority: 3, cores: 4, memoryMb: 16384, queuedTime: "1m 12s ago" },
    { id: "task-105", jobName: "Log-Indexing-Elastic", priority: 1, cores: 2, memoryMb: 8192, queuedTime: "5m ago" },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Configuration column */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Scheduler Engine Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Scheduling Policy</label>
            <div className="flex flex-col gap-2">
              <Button 
                variant={algo === 'PRIORITY' ? 'primary' : 'outline'} 
                className="w-full justify-start"
                onClick={() => setAlgo('PRIORITY')}
              >
                ⭐ Priority-Based Preemptive
              </Button>
              <Button 
                variant={algo === 'FIFO' ? 'primary' : 'outline'} 
                className="w-full justify-start"
                onClick={() => setAlgo('FIFO')}
              >
                ⏱️ First-In, First-Out (FIFO)
              </Button>
              <Button 
                variant={algo === 'FAIR' ? 'primary' : 'outline'} 
                className="w-full justify-start"
                onClick={() => setAlgo('FAIR')}
              >
                ⚖️ Fair Share Allocator
              </Button>
            </div>
          </div>

          <div className="pt-4 border-t border-border space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-medium">
                <span className="text-muted-foreground">MAX CONCURRENT TASKS</span>
                <span className="text-primary">128</span>
              </div>
              <input type="range" className="w-full accent-indigo-500" min="10" max="500" defaultValue="128" />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5 font-medium">
                <span className="text-muted-foreground">HEARTBEAT TIMEOUT LIMIT</span>
                <span className="text-cyan-600">30s</span>
              </div>
              <input type="range" className="w-full accent-cyan-400" min="5" max="120" defaultValue="30" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Queue items column */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Scheduler Priority Queue (Pending Tasks)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {queueItems.map((item) => (
              <div key={item.id} className="p-3.5 rounded border border-border bg-muted flex items-center justify-between hover:border-input transition-all">
                <div className="flex items-center gap-4">
                  <div className="px-2.5 py-1.5 rounded bg-primary/10 text-primary font-bold text-xs">
                    P{item.priority}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-muted-foreground">{item.jobName}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      ID: <span className="font-mono">{item.id}</span> • vCPUs: {item.cores} • Memory: {item.memoryMb / 1024} GB
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground font-semibold">{item.queuedTime}</div>
                  <div className="text-xs text-muted-foreground mt-1">Waiting in buffer</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
