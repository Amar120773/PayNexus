import React from 'react';
import { Job } from '../../../types';
import { StatusBadge } from '../../../components/ui/StatusBadge';
import { Button } from '../../../components/ui/Button';

interface JobTableProps {
  jobs: Job[];
  onSelectJob: (job: Job) => void;
  onCancelJob?: (id: string) => void;
  onRetryJob?: (id: string) => void;
}

export const JobTable: React.FC<JobTableProps> = ({
  jobs,
  onSelectJob,
  onCancelJob,
  onRetryJob,
}) => {
  if (jobs.length === 0) {
    return (
      <div className="bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 p-12 text-center text-muted-foreground text-sm">
        No jobs submitted to the cluster registry.
      </div>
    );
  }

  const getTaskProgress = (job: Job) => {
    const total = job.tasks ? job.tasks.length : 0;
    const completed = job.tasks ? job.tasks.filter(t => t.state === 'SUCCEEDED').length : 0;
    const failed = job.tasks ? job.tasks.filter(t => t.state === 'FAILED').length : 0;
    return { total, completed, failed };
  };

  return (
    <div className="overflow-x-auto border border-border bg-background rounded-lg shadow-xl">
      <table className="min-w-full divide-y divide-border text-left text-sm text-muted-foreground">
        <thead className="bg-muted text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          <tr>
            <th className="px-6 py-4">Job ID / Name</th>
            <th className="px-6 py-4">Priority</th>
            <th className="px-6 py-4">Status</th>
            <th className="px-6 py-4">Task Graph Progress</th>
            <th className="px-6 py-4">Submitted At</th>
            <th className="px-6 py-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card">
          {jobs.map((job) => {
            const { total, completed, failed } = getTaskProgress(job);
            const progressPercent = total > 0 ? (completed / total) * 100 : 0;
            const failedPercent = total > 0 ? (failed / total) * 100 : 0;

            return (
              <tr 
                key={job.id} 
                className="hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => onSelectJob(job)}
              >
                <td className="px-6 py-4">
                  <div className="font-semibold text-foreground font-mono text-xs">{job.id}</div>
                  <div className="text-muted-foreground text-xs mt-0.5">{job.name}</div>
                </td>
                <td className="px-6 py-4 font-mono font-bold text-primary">
                  P-{job.priority}
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={job.state} />
                </td>
                <td className="px-6 py-4 max-w-[200px]" onClick={e => e.stopPropagation()}>
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                    <span>{completed} / {total} Tasks</span>
                    {failed > 0 && <span className="text-destructive">{failed} Failed</span>}
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2 overflow-hidden flex">
                    <div 
                      className="bg-emerald-500 h-full" 
                      style={{ width: `${progressPercent}%` }}
                    />
                    <div 
                      className="bg-red-500 h-full" 
                      style={{ width: `${failedPercent}%` }}
                    />
                  </div>
                </td>
                <td className="px-6 py-4 text-xs font-mono text-muted-foreground">
                  {job.createdAt ? new Date(job.createdAt).toLocaleTimeString() : '-'}
                </td>
                <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                  <div className="flex gap-2 justify-end">
                    {(job.state === 'FAILED' || job.state === 'CANCELLED') && onRetryJob && (
                      <Button
                        variant="primary"
                        className="px-2.5 py-1 text-xs h-7 bg-primary text-primary-foreground hover:bg-primary/90 border-none"
                        onClick={() => onRetryJob(job.id!)}
                      >
                        Retry
                      </Button>
                    )}
                    {(job.state === 'PENDING' || job.state === 'RUNNING') && onCancelJob && (
                      <Button
                        variant="outline"
                        className="px-2.5 py-1 text-xs h-7 border-destructive/30 text-destructive hover:bg-destructive/10"
                        onClick={() => onCancelJob(job.id!)}
                      >
                        Cancel
                      </Button>
                    )}
                    <Button 
                      variant="outline"
                      className="px-2.5 py-1 text-xs h-7 border-border text-muted-foreground hover:bg-secondary/40"
                      onClick={() => onSelectJob(job)}
                    >
                      Details
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
