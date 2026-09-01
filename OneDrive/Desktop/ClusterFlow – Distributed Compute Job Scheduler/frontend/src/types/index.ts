export type UserRole = 'admin' | 'operator' | 'viewer';

export interface Credentials {
  email: string;
  password?: string;
}

export interface User {
  id: string;
  email: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export interface TokenResponse {
  token: string;
  expiresAt: string;
  user: User;
}

export type JobState = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';

export interface Task {
  id: string;
  name: string;
  command: string;
  state: JobState;
  assignedNode?: string;
  dependsOn: string[];
  exitCode: number;
  errorLog?: string;
  startedAt?: string;
  finishedAt?: string;
}

export interface Job {
  id?: string;
  name: string;
  description: string;
  creatorId?: string;
  priority: number;
  state: JobState;
  tasks: Task[];
  variables: Record<string, string>;
  createdAt?: string;
  updatedAt?: string;
  startedAt?: string;
  finishedAt?: string;
}

export type WorkerState = 'ACTIVE' | 'IDLE' | 'MAINTENANCE' | 'OFFLINE';

export interface ResourceStats {
  cpuCores: number;
  cpuUsagePercent: number;
  totalMemoryBytes: number;
  usedMemoryBytes: number;
  totalDiskBytes: number;
  usedDiskBytes: number;
}

export interface WorkerNode {
  id: string;
  hostname: string;
  ipAddress: string;
  state: WorkerState;
  resources: ResourceStats;
  runningTasks: string[];
  lastHeartbeat: string;
  joinedAt: string;
}

export interface WebSocketMessage<T = unknown> {
  event: string;
  payload: T;
}
