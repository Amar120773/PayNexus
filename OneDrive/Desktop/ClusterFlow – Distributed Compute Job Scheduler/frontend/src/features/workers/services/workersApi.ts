import api from '../../../services/api';
import { WorkerNode } from '../../../types';

export const workersApi = {
  list: async (): Promise<WorkerNode[]> => {
    const response = await api.get<WorkerNode[]>('/workers');
    return response.data;
  },
};
