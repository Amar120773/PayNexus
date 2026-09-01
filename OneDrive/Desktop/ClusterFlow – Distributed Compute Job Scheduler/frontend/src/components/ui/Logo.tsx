import React from 'react';

export const Logo: React.FC<{ className?: string }> = ({ className = 'h-6 w-6' }) => {
  return (
    <svg 
      className={`${className} text-primary`} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2.5" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    >
      {/* Master Scheduler Central Node */}
      <circle cx="12" cy="6" r="3" className="fill-primary/20" />
      
      {/* Worker Nodes */}
      <circle cx="5" cy="18" r="2" />
      <circle cx="12" cy="18" r="2" />
      <circle cx="19" cy="18" r="2" />
      
      {/* Dotted lines representing flow of jobs */}
      <path d="M12 9v7" strokeDasharray="2 2" />
      <path d="M12 9L6.5 16.5" strokeDasharray="2 2" />
      <path d="M12 9l5.5 7.5" strokeDasharray="2 2" />
    </svg>
  );
};
