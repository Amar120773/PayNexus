import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { WorkerNode } from '../../../types';
import { workersApi } from '../services/workersApi';
import { useWebSocket } from '../../../context/WebSocketContext';

export const useWorkers = () => {
  const { subscribe } = useWebSocket();
  const queryClient = useQueryClient();

  const { data: workersList = [], isLoading, error } = useQuery<WorkerNode[]>({
    queryKey: ['workers'],
    queryFn: workersApi.list,
  });

  useEffect(() => {
    const invalidate = () => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
    };

    const handleHeartbeat = (payload: { workerId: string; resources: any; runningTasks: string[] }) => {
      queryClient.setQueryData<WorkerNode[]>(['workers'], (prev = []) =>
        prev.map((node) => {
          if (node.id === payload.workerId) {
            return {
              ...node,
              resources: payload.resources,
              runningTasks: payload.runningTasks || [],
              lastHeartbeat: new Date().toISOString(),
              state: 'ACTIVE',
            };
          }
          return node;
        })
      );
    };

    const unsubReg = subscribe('worker_registered', invalidate);
    const unsubHb = subscribe('worker_heartbeat', handleHeartbeat);
    const unsubOff = subscribe('worker_went_offline', invalidate);

    return () => {
      unsubReg();
      unsubHb();
      unsubOff();
    };
  }, [subscribe, queryClient]);

  return {
    workersList: workersList || [],
    isLoading,
    error: error ? (error as any).response?.data?.error || 'Failed to fetch workers' : null,
    refetch: () => queryClient.invalidateQueries({ queryKey: ['workers'] }),
  };
};
