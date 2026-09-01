import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Job } from '../../../types';
import { jobsApi } from '../services/jobsApi';
import { useWebSocket } from '../../../context/WebSocketContext';

export const useJobs = (filterState?: string) => {
  const { subscribe } = useWebSocket();
  const queryClient = useQueryClient();

  const { data: jobsList = [], isLoading, error } = useQuery<Job[]>({
    queryKey: ['jobs', filterState],
    queryFn: () => jobsApi.list(filterState),
  });

  useEffect(() => {
    const handleUpdate = () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    };

    const unsubSubmit = subscribe('job_submitted', handleUpdate);
    const unsubUpdate = subscribe('job_state_updated', handleUpdate);
    const unsubCancel = subscribe('job_cancelled', handleUpdate);

    return () => {
      unsubSubmit();
      unsubUpdate();
      unsubCancel();
    };
  }, [subscribe, queryClient]);

  const submitMutation = useMutation({
    mutationFn: jobsApi.submit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: jobsApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: jobsApi.retry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  return {
    jobsList: jobsList || [],
    isLoading,
    error: error ? (error as any).response?.data?.error || 'Failed to fetch jobs' : null,
    refetch: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
    submitJob: submitMutation.mutateAsync,
    cancelJob: cancelMutation.mutateAsync,
    retryJob: retryMutation.mutateAsync,
    isSubmitting: submitMutation.isPending,
    isCancelling: cancelMutation.isPending,
    isRetrying: retryMutation.isPending,
  };
};
