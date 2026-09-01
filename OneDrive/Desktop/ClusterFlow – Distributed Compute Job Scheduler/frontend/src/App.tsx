import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { WebSocketProvider, useWebSocket } from './context/WebSocketContext';
import { Navbar } from './components/layout/Navbar';
import { LoginForm } from './features/auth/components/LoginForm';
import { RegisterForm } from './features/auth/components/RegisterForm';
import { useJobs } from './features/jobs/hooks/useJobs';
import { useWorkers } from './features/workers/hooks/useWorkers';
import { useStore, AlertMessage } from './store/useStore';
import { telemetryApi } from './features/telemetry/services/telemetryApi';
import { schedulerApi } from './features/scheduler/services/schedulerApi';
import { Button } from './components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/Card';
import { TableSkeleton } from './components/ui/Skeleton';
import { ErrorBanner } from './components/ui/ErrorBanner';
import { TelemetryChart } from './components/ui/TelemetryChart';
import { JobTable } from './features/jobs/components/JobTable';
import { JobTimeline } from './features/jobs/components/JobTimeline';
import { WorkerCard } from './features/workers/components/WorkerCard';
import { MetricsCardGrid } from './features/telemetry/components/MetricsCardGrid';
import { QueueTable } from './features/scheduler/components/QueueTable';
import { Job, Task } from './types';


import { Logo } from './components/ui/Logo';

// Auth Protection Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = useStore((state: any) => state.token);
  const alerts = useStore((state: any) => state.alerts);
  const clearAlerts = useStore((state: any) => state.clearAlerts);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Navbar />
      {/* Real-time Alerts Banner (WebSocket-driven) */}
      {alerts.length > 0 && (
        <div className="max-w-7xl w-full mx-auto px-6 pt-6">
          <div className="border border-destructive/20 bg-destructive/10 rounded-lg p-4 flex justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <span className="text-xl animate-bounce">🚨</span>
              <div className="text-xs">
                <span className="font-bold text-destructive">CRITICAL ERROR REPORTED:</span>{' '}
                <span className="text-muted-foreground">
                  Task {alerts[0].taskId} inside job {alerts[0].jobId} failed! {alerts[0].error}
                </span>
              </div>
            </div>
            <button 
              className="text-xs text-destructive hover:text-destructive/80 font-semibold underline"
              onClick={clearAlerts}
            >
              Clear Logs
            </button>
          </div>
        </div>
      )}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('cf_token'));

  useEffect(() => {
    const handleAuthChange = () => {
      setIsAuthenticated(!!localStorage.getItem('cf_token'));
    };
    window.addEventListener('auth_login', handleAuthChange);
    window.addEventListener('auth_logout', handleAuthChange);
    return () => {
      window.removeEventListener('auth_login', handleAuthChange);
      window.removeEventListener('auth_logout', handleAuthChange);
    };
  }, []);

  return (
    <WebSocketProvider>
      <WebSocketAlertListener />
      <Router>
        <Routes>
          {/* Auth Route */}
          <Route 
            path="/login" 
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <AuthPage onSuccess={() => setIsAuthenticated(true)} />
              )
            } 
          />

          {/* Protected Main Shell */}
          <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/jobs" element={<ProtectedRoute><JobsPage /></ProtectedRoute>} />
          <Route path="/workers" element={<ProtectedRoute><WorkersPage /></ProtectedRoute>} />
          <Route path="/scheduler" element={<ProtectedRoute><SchedulerPage /></ProtectedRoute>} />
          <Route path="/telemetry" element={<ProtectedRoute><TelemetryPage /></ProtectedRoute>} />
          <Route path="/cluster" element={<ProtectedRoute><ClusterPage /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />

          {/* Fallback routing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </WebSocketProvider>
  );
};

// WebSocket failure notifications listener
const WebSocketAlertListener: React.FC = () => {
  const { subscribe } = useWebSocket();
  const addAlert = useStore((state: any) => state.addAlert);

  useEffect(() => {
    const unsubscribe = subscribe('failure_notification', (payload: any) => {
      addAlert({
        jobId: payload.jobId,
        taskId: payload.taskId,
        error: payload.error || 'Execution status returns exit code 1',
      });
    });
    return () => unsubscribe();
  }, [subscribe, addAlert]);

  return null;
};

const AuthPage: React.FC<{ onSuccess: () => void }> = ({ onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-4 overflow-hidden bg-slate-50">
      {/* Decorative dot pattern */}
      <div className="absolute inset-0 -z-10 h-full w-full bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:16px_16px]"></div>
      
      {/* Glowing backdrop blur */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 -z-10 w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px] pointer-events-none"></div>

      <div className="flex flex-col items-center gap-6 z-10 w-full max-w-md">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-card border border-border shadow-sm">
            <Logo className="h-6 w-6" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
            ClusterFlow
          </h1>
          <p className="text-xs text-muted-foreground font-medium">
            Distributed Compute Job Scheduler
          </p>
        </div>

        {isRegister ? (
          <RegisterForm onSuccess={onSuccess} onToggleForm={() => setIsRegister(false)} />
        ) : (
          <LoginForm onSuccess={onSuccess} onToggleForm={() => setIsRegister(true)} />
        )}
      </div>
    </div>
  );
};

const DashboardPage: React.FC = () => {
  const { subscribe } = useWebSocket();
  const queryClient = useQueryClient();

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['clusterStatus'],
    queryFn: telemetryApi.getClusterStatus,
  });

  const { data: metricsData } = useQuery({
    queryKey: ['telemetryMetrics'],
    queryFn: telemetryApi.getMetrics,
  });

  const { jobsList, isLoading: jobsLoading, cancelJob, retryJob } = useJobs();
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  useEffect(() => {
    const handleStats = () => {
      queryClient.invalidateQueries({ queryKey: ['clusterStatus'] });
    };
    const handleMetrics = () => {
      queryClient.invalidateQueries({ queryKey: ['telemetryMetrics'] });
    };
    const unsubHb = subscribe('worker_heartbeat', handleStats);
    const unsubMetrics = subscribe('metrics_updated', () => {
      handleStats();
      handleMetrics();
    });

    return () => {
      unsubHb();
      unsubMetrics();
    };
  }, [subscribe, queryClient]);

  if (statsLoading || jobsLoading) {
    return <TableSkeleton rows={8} />;
  }

  if (statsError || !stats) {
    return <ErrorBanner message={statsError ? (statsError as any).message : 'Failed to reach cluster telemetry'} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">Cluster Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">Real-time status metrics of distributed computational tasks.</p>
        </div>
        <Link to="/jobs">
          <Button variant="primary">Configure Jobs</Button>
        </Link>
      </div>

      <MetricsCardGrid stats={stats} />

      {/* Live CPU & Memory Utilization Graphs directly on Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TelemetryChart 
          data={metricsData || []} 
          metricKey="clusterCpuPercent" 
          title="Cluster CPU Utilization" 
          color="#06b6d4" 
          fillColor="rgba(6,182,212,0.05)" 
          suffix="%" 
          maxVal={100}
        />
        <TelemetryChart 
          data={metricsData || []} 
          metricKey="clusterUsedMemoryBytes" 
          title="Cluster Memory Utilization" 
          color="#a855f7" 
          fillColor="rgba(168,85,247,0.05)" 
          suffix=" Bytes"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-foreground">Active Queue Monitor</h3>
          <JobTable 
            jobs={jobsList.slice(0, 5)} 
            onSelectJob={setSelectedJob} 
            onCancelJob={cancelJob}
            onRetryJob={retryJob}
          />
        </div>
        <div className="lg:col-span-1 bg-card text-card-foreground border border-border rounded-xl shadow-sm p-6 space-y-4 flex flex-col justify-center text-center">
          <span className="text-4xl">🌀</span>
          <h3 className="text-lg font-semibold text-muted-foreground">Distributed Scheduler Active</h3>
          <p className="text-muted-foreground text-xs leading-relaxed">
            Matching nodes are active in priority queue matching. Monitor latency distributions or update dispatch policies in the Settings/Queue panels.
          </p>
          <div className="flex gap-2 justify-center pt-2">
            <Link to="/scheduler">
              <Button variant="outline" className="text-xs">Scheduling Policies</Button>
            </Link>
            <Link to="/telemetry">
              <Button variant="outline" className="text-xs">Live Telemetry</Button>
            </Link>
          </div>
        </div>
      </div>

      {selectedJob && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg max-w-2xl w-full p-6 space-y-4 overflow-y-auto max-h-[85vh]">
            <div className="flex justify-between items-center border-b border-border pb-3">
              <h3 className="text-lg font-semibold text-foreground font-mono">{selectedJob.id}</h3>
              <button className="text-muted-foreground hover:text-foreground" onClick={() => setSelectedJob(null)}>✕</button>
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-muted-foreground">{selectedJob.name}</h4>
              <p className="text-muted-foreground text-xs">{selectedJob.description}</p>
            </div>
            <div className="border-t border-border pt-3">
              <h5 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wider">Subtask Steps DAG</h5>
              <JobTimeline tasks={selectedJob.tasks || []} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const JobsPage: React.FC = () => {
  const { jobsList, isLoading, error, submitJob, cancelJob, retryJob } = useJobs();
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  if (isLoading) return <TableSkeleton rows={8} />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Compute Jobs Registry</h1>
          <p className="text-muted-foreground text-sm mt-1">Submit, monitor, and abort executing task graphs.</p>
        </div>
        <Button variant="primary" onClick={() => setShowSubmitModal(true)}>
          Submit Compute Flow
        </Button>
      </div>

      <JobTable 
        jobs={jobsList} 
        onSelectJob={setSelectedJob} 
        onCancelJob={cancelJob} 
        onRetryJob={retryJob} 
      />

      {showSubmitModal && (
        <SubmitJobModal 
          onClose={() => setShowSubmitModal(false)} 
          onSubmit={submitJob} 
        />
      )}

      {selectedJob && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg max-w-2xl w-full p-6 space-y-4 overflow-y-auto max-h-[85vh]">
            <div className="flex justify-between items-center border-b border-border pb-3">
              <h3 className="text-lg font-semibold text-foreground font-mono">{selectedJob.id}</h3>
              <button className="text-muted-foreground hover:text-foreground" onClick={() => setSelectedJob(null)}>✕</button>
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-muted-foreground">{selectedJob.name}</h4>
              <p className="text-muted-foreground text-xs">{selectedJob.description}</p>
            </div>
            <div className="border-t border-border pt-3">
              <h5 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wider">Subtask Steps DAG</h5>
              <JobTimeline tasks={selectedJob.tasks || []} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const SubmitJobModal: React.FC<{ onClose: () => void; onSubmit: (job: Job) => Promise<any> }> = ({ onClose, onSubmit }) => {
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [priority, setPriority] = useState(1);
  const [tasks, setTasks] = useState<Task[]>([
    { id: 'task-1', name: 'Initialization', command: 'sleep 5', state: 'PENDING', dependsOn: [], exitCode: 0 }
  ]);
  const [error, setError] = useState('');

  const addTask = () => {
    const nextId = `task-${tasks.length + 1}`;
    setTasks([...tasks, { id: nextId, name: `Task Step ${tasks.length + 1}`, command: 'sleep 5', state: 'PENDING', dependsOn: [], exitCode: 0 }]);
  };

  const handleTaskChange = (index: number, key: keyof Task, val: any) => {
    setTasks(tasks.map((t, idx) => (idx === index ? { ...t, [key]: val } : t)));
  };

  const handleDependsChange = (index: number, value: string) => {
    const depends = value.split(',').map(s => s.trim()).filter(s => s !== '');
    handleTaskChange(index, 'dependsOn', depends);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return setError('Job Name is required');

    const jobPayload: Job = {
      name,
      description: desc,
      priority: Number(priority),
      state: 'PENDING',
      tasks,
      variables: {},
    };

    try {
      await onSubmit(jobPayload);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to submit compute flow');
    }
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <form onSubmit={handleFormSubmit} className="bg-card border border-border rounded-lg max-w-2xl w-full p-6 space-y-4 overflow-y-auto max-h-[85vh]">
        <div className="flex justify-between items-center border-b border-border pb-3">
          <h3 className="text-lg font-semibold text-foreground">Submit Computational Flow</h3>
          <button type="button" className="text-muted-foreground hover:text-foreground" onClick={onClose}>✕</button>
        </div>

        {error && <div className="p-3 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive">{error}</div>}

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Job Name</label>
            <input type="text" className="w-full bg-background border border-border rounded px-3 py-2 text-xs text-foreground" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. ResNet-Train" />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Scheduler Priority (1-10)</label>
            <input type="number" min="1" max="10" className="w-full bg-background border border-border rounded px-3 py-2 text-xs text-foreground" value={priority} onChange={e => setPriority(Number(e.target.value))} />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Description</label>
          <textarea className="w-full bg-background border border-border rounded px-3 py-2 text-xs text-foreground h-20" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Provide task graph specifications" />
        </div>

        <div className="border-t border-border pt-3 space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Task Pipeline Definition</h4>
            <Button type="button" variant="outline" className="h-7 text-xs px-2.5" onClick={addTask}>+ Add Task</Button>
          </div>

          <div className="space-y-3 max-h-[250px] overflow-y-auto pr-1">
            {tasks.map((task, idx) => (
              <div key={idx} className="p-3 bg-background border border-border rounded space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <input type="text" className="bg-card border border-border rounded px-2.5 py-1 text-xs text-foreground font-mono" value={task.id} onChange={e => handleTaskChange(idx, 'id', e.target.value)} placeholder="task-id" />
                  <input type="text" className="bg-card border border-border rounded px-2.5 py-1 text-xs text-foreground" value={task.name} onChange={e => handleTaskChange(idx, 'name', e.target.value)} placeholder="Task Name" />
                  <input type="text" className="bg-card border border-border rounded px-2.5 py-1 text-xs text-foreground" value={task.command} onChange={e => handleTaskChange(idx, 'command', e.target.value)} placeholder="Shell Command" />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-muted-foreground font-mono">Dependencies (comma separated task IDs, e.g. task-1, task-2)</label>
                  <input type="text" className="w-full bg-card border border-border rounded px-2.5 py-1 text-xs text-muted-foreground font-mono" value={task.dependsOn.join(', ')} onChange={e => handleDependsChange(idx, e.target.value)} placeholder="None" />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3 justify-end pt-3 border-t border-border">
          <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary">Submit Job</Button>
        </div>
      </form>
    </div>
  );
};

const WorkersPage: React.FC = () => {
  const { workersList, isLoading, error } = useWorkers();

  if (isLoading) return <TableSkeleton rows={8} />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Active Worker Nodes</h1>
        <p className="text-muted-foreground text-sm mt-1">Compute agents registered across the distributed clusters.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workersList.map((worker: any) => (
          <WorkerCard key={worker.id} worker={worker} />
        ))}
      </div>
    </div>
  );
};

const SchedulerPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();

  const { data: queueData, isLoading, error } = useQuery({
    queryKey: ['schedulerQueue'],
    queryFn: schedulerApi.getQueue,
  });

  const policyMutation = useMutation({
    mutationFn: schedulerApi.setPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedulerQueue'] });
    },
  });

  useEffect(() => {
    const handleQueueChange = () => {
      queryClient.invalidateQueries({ queryKey: ['schedulerQueue'] });
    };
    const unsubQ = subscribe('queue_changed', handleQueueChange);
    return () => unsubQ();
  }, [subscribe, queryClient]);

  if (isLoading) return <TableSkeleton rows={8} />;
  if (error) return <ErrorBanner message={(error as any).message} />;

  const queueItems = queueData?.queueItems || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Queues & Dispatch Policies</h1>
        <p className="text-muted-foreground text-sm mt-1">Fine-tune task allocations and inspect scheduling waiting lists.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-foreground">Persistent Wait Queue ({queueItems.length} jobs)</h3>
          <QueueTable items={queueItems} />
        </div>

        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Sort & Dispatch Overrides</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Queueing Sorting Rule</label>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    className="flex-1 text-xs" 
                    onClick={() => policyMutation.mutate({ queuePolicy: 'FIFO' })}
                  >
                    FIFO Sort
                  </Button>
                  <Button 
                    variant="outline" 
                    className="flex-1 text-xs"
                    onClick={() => policyMutation.mutate({ queuePolicy: 'PRIORITY' })}
                  >
                    Priority Sort
                  </Button>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-border">
                <label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Node Placement Strategy</label>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    className="flex-1 text-xs"
                    onClick={() => policyMutation.mutate({ placementPolicy: 'FIRST_FIT' })}
                  >
                    First Fit
                  </Button>
                  <Button 
                    variant="outline" 
                    className="flex-1 text-xs"
                    onClick={() => policyMutation.mutate({ placementPolicy: 'LEAST_LOADED' })}
                  >
                    Least Loaded
                  </Button>
                </div>
              </div>

              {policyMutation.isPending && (
                <div className="text-xs text-primary animate-pulse text-center pt-2">Updating scheduling policies...</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const TelemetryPage: React.FC = () => {
  const { subscribe } = useWebSocket();
  const queryClient = useQueryClient();

  const { data: metricsData, isLoading, error } = useQuery({
    queryKey: ['telemetryMetrics'],
    queryFn: telemetryApi.getMetrics,
  });

  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const handleUpdate = () => {
      queryClient.invalidateQueries({ queryKey: ['telemetryMetrics'] });
    };

    const unsubMetrics = subscribe('metrics_updated', handleUpdate);
    const unsubTask = subscribe('task_state_updated', (payload: any) => {
      const now = new Date().toLocaleTimeString();
      setLogs((prev) => [`[${now}] Task ${payload.taskId} updated state to ${payload.state}`, ...prev].slice(0, 10));
    });

    return () => {
      unsubMetrics();
      unsubTask();
    };
  }, [subscribe, queryClient]);

  if (isLoading) return <TableSkeleton rows={8} />;
  if (error) return <ErrorBanner message={(error as any).message} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Cluster Telemetry</h1>
        <p className="text-muted-foreground text-sm mt-1">Live timeseries metrics history and active scheduler log outputs.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TelemetryChart 
          data={metricsData || []} 
          metricKey="clusterCpuPercent" 
          title="Cluster Average CPU load" 
          color="#06b6d4" 
          fillColor="rgba(6,182,212,0.05)" 
          suffix="%" 
          maxVal={100}
        />
        <TelemetryChart 
          data={metricsData || []} 
          metricKey="clusterUsedMemoryBytes" 
          title="Memory utilization" 
          color="#a855f7" 
          fillColor="rgba(168,85,247,0.05)" 
          suffix=" Bytes"
        />
        <TelemetryChart 
          data={metricsData || []} 
          metricKey="queuedJobs" 
          title="Queues Buffer backlog" 
          color="#3b82f6" 
          fillColor="rgba(59,130,246,0.05)"
        />
        <TelemetryChart 
          data={metricsData || []} 
          metricKey="throughput" 
          title="Execution Processing throughput" 
          color="#10b981" 
          fillColor="rgba(16,185,129,0.05)" 
          suffix=" jobs/m"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider">
            <span className="h-2.5 w-2.5 bg-emerald-500 rounded-full animate-ping" />
            Live System Event Logs Stream
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-background border border-border rounded-md p-4 font-mono text-xs overflow-y-auto h-48 space-y-2 text-muted-foreground">
            {logs.length === 0 ? (
              <div className="text-muted-foreground italic">Listening for cluster task updates...</div>
            ) : (
              logs.map((log, idx) => <div key={idx}>{log}</div>)
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const ClusterPage: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['clusterStatus'],
    queryFn: telemetryApi.getClusterStatus,
  });

  if (isLoading) return <TableSkeleton rows={8} />;
  if (error || !stats) return <ErrorBanner message={error ? (error as any).message : 'Telemetry statistics unavailable'} />;

  const formatBytes = (bytes: number) => {
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Cluster Resource Pool</h1>
        <p className="text-muted-foreground text-sm mt-1">Aggregated hardware capabilities, active worker summaries, and specifications.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="py-6 space-y-2 select-text">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Total Cores Capacity</h4>
            <p className="text-4xl font-bold text-foreground font-mono">{stats.resources.totalCores} Cores</p>
            <p className="text-muted-foreground text-xs">Available for concurrent thread processing</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-6 space-y-2 select-text">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Cluster Memory Size</h4>
            <p className="text-4xl font-bold text-foreground font-mono">{formatBytes(stats.resources.totalMemoryBytes)}</p>
            <p className="text-muted-foreground text-xs">Used: {formatBytes(stats.resources.usedMemoryBytes)} ({((stats.resources.usedMemoryBytes / stats.resources.totalMemoryBytes) * 100).toFixed(1)}%)</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-6 space-y-2 select-text">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Workers</h4>
            <p className="text-4xl font-bold text-foreground font-mono">{stats.workers.online} / {stats.workers.total}</p>
            <p className="text-muted-foreground text-xs">Agents online across the cluster network</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Nodes Specs Capacity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-4 bg-card border border-border rounded-lg space-y-1">
              <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">Load Average</span>
              <p className="text-xl font-bold text-primary font-mono">{(stats.resources.avgCpuLoad || 0).toFixed(1)}%</p>
            </div>
            <div className="p-4 bg-card border border-border rounded-lg space-y-1">
              <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">Succeeded Tasks</span>
              <p className="text-xl font-bold text-emerald-600 font-mono">{stats.jobs.succeeded}</p>
            </div>
            <div className="p-4 bg-card border border-border rounded-lg space-y-1">
              <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">Active Executions</span>
              <p className="text-xl font-bold text-cyan-600 font-mono">{stats.jobs.running}</p>
            </div>
            <div className="p-4 bg-card border border-border rounded-lg space-y-1">
              <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">Fail Logs</span>
              <p className="text-xl font-bold text-destructive font-mono">{stats.jobs.failed}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const SettingsPage: React.FC = () => {
  const { settings, updateSettings, alerts, clearAlerts } = useStore();

  const handleRefreshChange = (val: string) => {
    updateSettings({ refreshInterval: Number(val) });
  };

  const handleThemeChange = (val: 'dark' | 'light') => {
    updateSettings({ theme: val });
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-sans">Dashboard Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">Configure dashboard interfaces, refresh speeds, and inspect alerts logs.</p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Dashboard Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground">REST Gateway API Server URL</h4>
                <p className="text-muted-foreground text-xs mt-1">Address used by Axios clients to trigger commands</p>
              </div>
              <input 
                type="text" 
                className="bg-background border border-border rounded px-3 py-1.5 text-xs font-mono text-muted-foreground w-64"
                value={settings.serverUrl}
                onChange={e => updateSettings({ serverUrl: e.target.value })}
              />
            </div>

            <div className="flex items-center justify-between py-2 border-t border-border">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground">Telemetry Poll Interval</h4>
                <p className="text-muted-foreground text-xs mt-1">Metrics polling latency rate (milliseconds)</p>
              </div>
              <select
                className="bg-background border border-border rounded px-3 py-1.5 text-xs text-muted-foreground w-32"
                value={settings.refreshInterval}
                onChange={e => handleRefreshChange(e.target.value)}
              >
                <option value="2000">2000ms</option>
                <option value="5000">5000ms</option>
                <option value="10000">10000ms</option>
              </select>
            </div>

            <div className="flex items-center justify-between py-2 border-t border-border">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground">UI Color Theme Mode</h4>
                <p className="text-muted-foreground text-xs mt-1">Toggle dark and light color tokens</p>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className={`px-3.5 py-1 h-8 text-xs ${settings.theme === 'dark' ? 'bg-primary border-none' : ''}`}
                  onClick={() => handleThemeChange('dark')}
                >
                  Dark Cyber
                </Button>
                <Button 
                  variant="outline" 
                  className={`px-3.5 py-1 h-8 text-xs ${settings.theme === 'light' ? 'bg-primary border-none' : ''}`}
                  onClick={() => handleThemeChange('light')}
                >
                  Light Classic
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex justify-between items-center flex-row">
            <CardTitle>WebSocket Diagnostics Alerts Log ({alerts.length})</CardTitle>
            {alerts.length > 0 && (
              <Button variant="outline" className="h-8 text-xs text-destructive border-destructive/20" onClick={clearAlerts}>
                Purge Log
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <p className="text-muted-foreground text-xs italic">No error alarms pushed in this session.</p>
            ) : (
              <div className="space-y-3 font-mono text-xs max-h-60 overflow-y-auto">
                {alerts.map((alert: AlertMessage) => (
                  <div key={alert.id} className="p-3 bg-red-500/5 border border-red-500/10 rounded flex justify-between gap-4">
                    <div>
                      <span className="text-destructive font-bold">[{alert.timestamp}]</span>{' '}
                      <span className="text-muted-foreground">Job: {alert.jobId} (Task: {alert.taskId}) failed. {alert.error}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
