import React from 'react';
import { QueueItem } from '../services/schedulerApi';
import { StatusBadge } from '../../../components/ui/StatusBadge';

interface QueueTableProps {
  items: QueueItem[];
}

export const QueueTable: React.FC<QueueTableProps> = ({ items }) => {
  if (items.length === 0) {
    return (
      <div className="bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 p-12 text-center text-muted-foreground text-sm">
        Scheduler queue buffer is currently empty.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-border bg-background rounded-lg shadow-xl">
      <table className="min-w-full divide-y divide-border text-left text-sm text-muted-foreground">
        <thead className="bg-muted text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          <tr>
            <th className="px-6 py-4">Rank / Position</th>
            <th className="px-6 py-4">Job ID</th>
            <th className="px-6 py-4">Sort Priority</th>
            <th className="px-6 py-4">Status</th>
            <th className="px-6 py-4">Queue Admission Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card font-mono text-xs">
          {items.map((item, index) => (
            <tr key={item.jobId} className="hover:bg-muted/50 transition-colors">
              <td className="px-6 py-4 font-semibold text-foreground">
                #{index + 1}
              </td>
              <td className="px-6 py-4 text-muted-foreground">
                {item.jobId}
              </td>
              <td className="px-6 py-4 font-bold text-primary">
                P-{item.priority}
              </td>
              <td className="px-6 py-4">
                <StatusBadge status={item.status} />
              </td>
              <td className="px-6 py-4 text-muted-foreground">
                {new Date(item.enqueuedAt).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
