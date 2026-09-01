import api from '../../../services/api';

export interface QueueItem {
  jobId: string;
  priority: number;
  status: string;
  enqueuedAt: string;
}

export const schedulerApi = {
  getQueue: async (): Promise<any> => {
    const response = await api.get<any>('/scheduler/queue');
    return response.data;
  },
  setPolicy: async (payload: { queuePolicy?: string; placementPolicy?: string }): Promise<any> => {
    const response = await api.post<any>('/scheduler/policy', payload);
    return response.data;
  },
};
