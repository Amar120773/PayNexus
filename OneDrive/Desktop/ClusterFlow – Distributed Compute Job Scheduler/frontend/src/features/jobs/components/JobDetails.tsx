import React from 'react';
import { Job } from '../../../types';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

interface JobDetailsProps {
  job: Job;
  onClose: () => void;
}

export const JobDetails: React.FC<JobDetailsProps> = ({ job, onClose }) => {
  const getTaskStateColor = (state: string) => {
    switch (state) {
      case 'PENDING': return 'text-muted-foreground bg-slate-500/10 border border-slate-500/20';
      case 'RUNNING': return 'text-primary bg-primary/10 border border-primary/20';
      case 'SUCCEEDED': return 'text-emerald-600 bg-emerald-500/10 border border-emerald-500/20';
      case 'FAILED': return 'text-destructive bg-destructive/10 border border-destructive/20';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <span className="text-xs font-semibold text-primary uppercase tracking-widest">Compute Job Details</span>
          <CardTitle className="text-xl mt-1">{job.name}</CardTitle>
        </div>
        <Button variant="outline" className="px-3 py-1 h-8 text-xs" onClick={onClose}>
          Back
        </Button>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Metadata info */}
        <div className="grid grid-cols-2 gap-4 text-xs border-b border-border pb-4">
          <div>
            <span className="text-muted-foreground block uppercase font-medium">Job Identity</span>
            <span className="text-muted-foreground font-mono select-all">{job.id}</span>
          </div>
          <div>
            <span className="text-muted-foreground block uppercase font-medium">State status</span>
            <span className="text-muted-foreground font-semibold">{job.state}</span>
          </div>
          <div>
            <span className="text-muted-foreground block uppercase font-medium">Priority queue level</span>
            <span className="text-muted-foreground">Level {job.priority}</span>
          </div>
          <div>
            <span className="text-muted-foreground block uppercase font-medium">Submitting user</span>
            <span className="text-muted-foreground">{job.creatorId || 'N/A'}</span>
          </div>
        </div>

        {/* Configuration variables */}
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Environment Configuration</h4>
          {Object.keys(job.variables).length > 0 ? (
            <div className="bg-background/40 border border-border p-3 rounded font-mono text-xs text-muted-foreground space-y-1">
              {Object.entries(job.variables).map(([k, v]) => (
                <div key={k}><span className="text-primary">{k}</span>={v}</div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground italic">No environment variables registered for this run context.</p>
          )}
        </div>

        {/* Tasks list */}
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Tasks Execution Chain (DAG)</h4>
          <div className="space-y-3">
            {job.tasks.map((task) => (
              <div key={task.id} className="p-3.5 rounded border border-border bg-muted flex items-center justify-between">
                <div>
                  <div className="font-semibold text-muted-foreground text-sm">{task.name}</div>
                  <div className="font-mono text-xs text-muted-foreground mt-1 bg-background/60 p-1.5 rounded inline-block">
                    $ {task.command}
                  </div>
                  {task.assignedNode && (
                    <div className="text-xs text-muted-foreground mt-2">
                      Assigned: <span className="font-mono text-primary">{task.assignedNode}</span>
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getTaskStateColor(task.state)}`}>
                    {task.state}
                  </span>
                  {task.exitCode !== 0 && task.state === 'FAILED' && (
                    <div className="text-xs text-destructive mt-1 font-semibold">Exit Code: {task.exitCode}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
