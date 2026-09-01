import React from 'react';
import { Job } from '../../../types';
import { Button } from '../../../components/ui/Button';

interface JobGridProps {
  jobs: Job[];
  onSelectJob: (job: Job) => void;
  onCancelJob: (id: string) => void;
}

export const JobGrid: React.FC<JobGridProps> = ({ jobs, onSelectJob, onCancelJob }) => {
  const getStateColor = (state: string) => {
    switch (state) {
      case 'PENDING': return 'bg-slate-500/20 text-muted-foreground border border-slate-500/30';
      case 'RUNNING': return 'bg-indigo-500/20 text-primary border border-indigo-500/30 pulse-success';
      case 'SUCCEEDED': return 'bg-emerald-500/20 text-emerald-600 border border-emerald-500/30';
      case 'FAILED': return 'bg-red-500/20 text-destructive border border-red-500/30';
      case 'CANCELLED': return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
      default: return 'bg-slate-700/25 text-muted-foreground';
    }
  };

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground border border-border rounded-lg bg-background/20">
        No compute jobs found in the queue database.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-left border-collapse bg-background/20">
        <thead>
          <tr className="border-b border-border text-xs text-muted-foreground font-semibold uppercase tracking-wider bg-muted">
            <th className="py-4 px-6">Job Identification</th>
            <th className="py-4 px-6">State</th>
            <th className="py-4 px-6">Priority</th>
            <th className="py-4 px-6">Execution Unit (Tasks)</th>
            <th className="py-4 px-6">Registered At</th>
            <th className="py-4 px-6 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 text-sm text-muted-foreground">
          {jobs.map((job) => (
            <tr key={job.id} className="hover:bg-white/5 transition-colors cursor-pointer" onClick={() => onSelectJob(job)}>
              <td className="py-4 px-6">
                <div className="font-semibold text-muted-foreground">{job.name}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{job.id}</div>
              </td>
              <td className="py-4 px-6">
                <span className={`px-2.5 py-1 rounded text-xs font-semibold ${getStateColor(job.state)}`}>
                  {job.state}
                </span>
              </td>
              <td className="py-4 px-6">
                <span className="text-muted-foreground font-medium">Lvl {job.priority}</span>
              </td>
              <td className="py-4 px-6">
                <span className="text-muted-foreground">{job.tasks.length} sub-tasks</span>
              </td>
              <td className="py-4 px-6 text-muted-foreground text-xs">
                {job.createdAt ? new Date(job.createdAt).toLocaleString() : 'N/A'}
              </td>
              <td className="py-4 px-6 text-right" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" className="px-2.5 py-1 h-7 text-xs" onClick={() => onSelectJob(job)}>
                    Inspect
                  </Button>
                  {(job.state === 'PENDING' || job.state === 'RUNNING') && (
                    <Button variant="danger" className="px-2.5 py-1 h-7 text-xs" onClick={() => job.id && onCancelJob(job.id)}>
                      Kill
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
