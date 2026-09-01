import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';

export const UtilizationGrid: React.FC = () => {
  // Mock data representing current load values
  const cpuLoad = 42.6;
  const memoryLoad = 68.2;
  const diskLoad = 34.1;

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle>System Utilization Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* CPU Util */}
        <div>
          <div className="flex justify-between text-xs mb-2 font-medium">
            <span className="text-muted-foreground">AVERAGE CLUSTER CPU LOAD</span>
            <span className="text-primary">{cpuLoad}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border">
            <div className="h-full bg-indigo-500 transition-all duration-500" style={{ width: `${cpuLoad}%` }} />
          </div>
        </div>

        {/* Memory Util */}
        <div>
          <div className="flex justify-between text-xs mb-2 font-medium">
            <span className="text-muted-foreground">TOTAL PROVISIONED MEMORY CONSUMPTION</span>
            <span className="text-cyan-600">{memoryLoad}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border">
            <div className="h-full bg-cyan-400 transition-all duration-500" style={{ width: `${memoryLoad}%` }} />
          </div>
        </div>

        {/* Disk Util */}
        <div>
          <div className="flex justify-between text-xs mb-2 font-medium">
            <span className="text-muted-foreground">EPHEMERAL DISK ALLOCATION</span>
            <span className="text-purple-400">{diskLoad}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border">
            <div className="h-full bg-purple-400 transition-all duration-500" style={{ width: `${diskLoad}%` }} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
