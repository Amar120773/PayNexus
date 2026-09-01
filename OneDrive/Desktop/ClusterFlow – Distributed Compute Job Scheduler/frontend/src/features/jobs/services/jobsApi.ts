import api from '../../../services/api';
import { Job } from '../../../types';

export const jobsApi = {
  list: async (state?: string): Promise<Job[]> => {
    const response = await api.get<Job[]>('/jobs', {
      params: state ? { state } : {},
    });
    return response.data;
  },
  get: async (id: string): Promise<Job> => {
    const response = await api.get<Job>(`/jobs/${id}`);
    return response.data;
  },
  submit: async (job: Job): Promise<Job> => {
    const response = await api.post<Job>('/jobs', job);
    return response.data;
  },
  cancel: async (id: string): Promise<{ status: string; jobId: string }> => {
    const response = await api.delete<{ status: string; jobId: string }>(`/jobs/${id}`);
    return response.data;
  },
  retry: async (id: string): Promise<Job> => {
    const response = await api.post<Job>(`/jobs/${id}/retry`);
    return response.data;
  },
};
