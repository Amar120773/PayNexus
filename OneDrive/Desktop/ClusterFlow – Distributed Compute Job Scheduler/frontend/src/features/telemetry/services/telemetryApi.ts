import api from '../../../services/api';

export interface MetricSnapshot {
	id: string;
	timestamp: string;
	clusterCpuPercent: number;
	clusterMemoryBytes: number;
	clusterUsedMemoryBytes: number;
	activeJobs: number;
	queuedJobs: number;
	failedJobs: number;
	throughput: number;
	onlineWorkers: number;
	totalWorkers: number;
}

export const telemetryApi = {
  getMetrics: async (): Promise<MetricSnapshot[]> => {
    const response = await api.get<MetricSnapshot[]>('/telemetry/metrics');
    return response.data;
  },
  getClusterStatus: async (): Promise<any> => {
    const response = await api.get<any>('/telemetry/status');
    return response.data;
  },
};
