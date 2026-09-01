import React from 'react';
import { MetricSnapshot } from '../../features/telemetry/services/telemetryApi';

interface ChartProps {
  data: MetricSnapshot[];
  metricKey: keyof Omit<MetricSnapshot, 'id' | 'timestamp'>;
  title: string;
  color?: string;
  fillColor?: string;
  suffix?: string;
  maxVal?: number;
}

export const TelemetryChart: React.FC<ChartProps> = ({
  data,
  metricKey,
  title,
  color = '#6366f1',
  fillColor = 'rgba(99, 102, 241, 0.05)',
  suffix = '',
  maxVal,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 p-6 h-64 flex items-center justify-center text-muted-foreground text-xs">
        No timeseries diagnostics logged yet.
      </div>
    );
  }

  const vals = data.map(d => Number(d[metricKey] || 0));
  const max = maxVal !== undefined ? maxVal : Math.max(...vals, 1);
  const min = Math.min(...vals, 0);
  const range = max - min === 0 ? 1 : max - min;

  const width = 600;
  const height = 180;
  const padding = 20;

  const points = vals.map((val, idx) => {
    const x = padding + (idx / (vals.length - 1)) * (width - padding * 2);
    const y = height - padding - ((val - min) / range) * (height - padding * 2);
    return { x, y, val };
  });

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaD = points.length > 0 
    ? `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`
    : '';

  return (
    <div className="bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 p-6 flex flex-col justify-between">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{title}</h4>
        <div className="text-xs font-mono font-semibold" style={{ color }}>
          Live: {vals[vals.length - 1].toFixed(1)}{suffix}
        </div>
      </div>

      <div className="relative w-full">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="rgba(255,255,255,0.03)" strokeDasharray="3" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="rgba(255,255,255,0.03)" strokeDasharray="3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="rgba(255,255,255,0.05)" />

          {areaD && (
            <path
              d={areaD}
              fill={fillColor}
            />
          )}

          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke={color}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {points.length < 25 && points.map((p, idx) => (
            <circle
              key={idx}
              cx={p.x}
              cy={p.y}
              r="3.5"
              fill="#0b0c14"
              stroke={color}
              strokeWidth="2"
            />
          ))}
        </svg>
      </div>

      <div className="flex justify-between text-[10px] text-muted-foreground font-mono mt-2 pt-2 border-t border-border">
        <span>{new Date(data[0].timestamp).toLocaleTimeString()}</span>
        <span>{new Date(data[Math.floor(data.length / 2)].timestamp).toLocaleTimeString()}</span>
        <span>{new Date(data[data.length - 1].timestamp).toLocaleTimeString()}</span>
      </div>
    </div>
  );
};
