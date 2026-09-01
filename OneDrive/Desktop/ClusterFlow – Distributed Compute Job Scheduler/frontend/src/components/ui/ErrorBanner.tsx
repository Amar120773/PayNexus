import React from 'react';
import { Button } from './Button';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onRetry }) => {
  return (
    <div className="border border-destructive/20 bg-destructive/10 rounded-lg p-6 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-[0_0_12px_rgba(239,68,68,0.08)]">
      <div className="flex items-center gap-3">
        <span className="text-3xl">⚠️</span>
        <div>
          <h4 className="text-destructive font-semibold text-sm">System Operations Failure</h4>
          <p className="text-muted-foreground text-xs mt-1">{message}</p>
        </div>
      </div>
      {onRetry && (
        <Button variant="outline" className="border-red-500/30 hover:bg-red-500/20 text-destructive text-xs py-1.5 h-8" onClick={onRetry}>
          Re-establish Connection
        </Button>
      )}
    </div>
  );
};
