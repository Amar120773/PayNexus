import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const normStatus = status.toUpperCase();

  let styles = 'bg-slate-500/10 text-muted-foreground border border-slate-500/20';

  if (normStatus === 'RUNNING') {
    styles = 'bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-[0_0_8px_rgba(59,130,246,0.1)]';
  } else if (normStatus === 'SUCCEEDED' || normStatus === 'ACTIVE') {
    styles = 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 shadow-[0_0_8px_rgba(16,185,129,0.1)]';
  } else if (normStatus === 'FAILED' || normStatus === 'OFFLINE') {
    styles = 'bg-destructive/10 text-destructive border border-destructive/20 shadow-[0_0_8px_rgba(239,68,68,0.1)]';
  } else if (normStatus === 'CANCELLED') {
    styles = 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
  } else if (normStatus === 'PENDING') {
    styles = 'bg-slate-500/10 text-muted-foreground border border-slate-500/20';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${styles}`}>
      <span className={`h-1.5 w-1.5 rounded-full mr-1.5 ${
        normStatus === 'RUNNING' ? 'bg-blue-400 animate-pulse' :
        (normStatus === 'SUCCEEDED' || normStatus === 'ACTIVE') ? 'bg-emerald-400' :
        (normStatus === 'FAILED' || normStatus === 'OFFLINE') ? 'bg-red-400' :
        normStatus === 'CANCELLED' ? 'bg-amber-400' : 'bg-slate-400'
      }`} />
      {status}
    </span>
  );
};
