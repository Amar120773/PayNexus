package workers

import (
	"context"
	"time"
	"clusterflow/jobs"
)

// WorkerState represents the node's cluster operating status.
type WorkerState string

const (
	StateActive      WorkerState = "ACTIVE"
	StateIdle        WorkerState = "IDLE"
	StateMaintenance WorkerState = "MAINTENANCE"
	StateOffline     WorkerState = "OFFLINE"
)

// ResourceStats represents hardware telemetry for CPU, RAM, and Disk capacity vs usage.
type ResourceStats struct {
	CPUCores         int     `json:"cpuCores" bson:"cpuCores"`
	CPUUsagePercent  float64 `json:"cpuUsagePercent" bson:"cpuUsagePercent"`
	TotalMemoryBytes int64   `json:"totalMemoryBytes" bson:"totalMemoryBytes"`
	UsedMemoryBytes  int64   `json:"usedMemoryBytes" bson:"usedMemoryBytes"`
	TotalDiskBytes   int64   `json:"totalDiskBytes" bson:"totalDiskBytes"`
	UsedDiskBytes    int64   `json:"usedDiskBytes" bson:"usedDiskBytes"`
}

// WorkerNode represents a registered compute worker machine in the cluster.
type WorkerNode struct {
	ID             string        `json:"id" bson:"_id,omitempty"`
	Hostname       string        `json:"hostname" bson:"hostname"`
	IPAddress      string        `json:"ipAddress" bson:"ipAddress"`
	State          WorkerState   `json:"state" bson:"state"`
	Resources      ResourceStats `json:"resources" bson:"resources"`
	RunningTasks   []string      `json:"runningTasks" bson:"runningTasks"` // Task IDs currently running on this worker
	LastHeartbeat  time.Time     `json:"lastHeartbeat" bson:"lastHeartbeat"`
	JoinedAt       time.Time     `json:"joinedAt" bson:"joinedAt"`
}

// FreeCores returns the estimated available CPU cores based on CPU usage percentage.
func (w *WorkerNode) FreeCores() int {
	free := float64(w.Resources.CPUCores) * (1.0 - (w.Resources.CPUUsagePercent / 100.0))
	if free < 0 {
		return 0
	}
	return int(free)
}

// FreeMemory returns the available memory in bytes on the node.
func (w *WorkerNode) FreeMemory() int64 {
	free := w.Resources.TotalMemoryBytes - w.Resources.UsedMemoryBytes
	if free < 0 {
		return 0
	}
	return free
}

// HeartbeatPayload is sent periodically by workers to report their live health metrics.
type HeartbeatPayload struct {
	WorkerID     string        `json:"workerId" binding:"required"`
	Resources    ResourceStats `json:"resources" binding:"required"`
	RunningTasks []string      `json:"runningTasks"`
}

// WorkerRepository provides capabilities for saving and querying worker configurations.
type WorkerRepository interface {
	Create(ctx context.Context, worker *WorkerNode) error
	FindByID(ctx context.Context, id string) (*WorkerNode, error)
	FindAll(ctx context.Context) ([]WorkerNode, error)
	Update(ctx context.Context, worker *WorkerNode) error
	Delete(ctx context.Context, id string) error
	UpdateHeartbeat(ctx context.Context, id string, stats ResourceStats, runningTasks []string) error
}

// Service defines orchestration actions for registering and monitoring workers.
type Service interface {
	RegisterWorker(ctx context.Context, node *WorkerNode) (*WorkerNode, error)
	ProcessHeartbeat(ctx context.Context, payload HeartbeatPayload) error
	GetActiveWorkers(ctx context.Context) ([]WorkerNode, error)
	GetWorkerByID(ctx context.Context, id string) (*WorkerNode, error)
	UpdateWorkerState(ctx context.Context, id string, state WorkerState) error
	CheckOfflineWorkers(ctx context.Context, timeout time.Duration) error
	// Polling and task execution reporting
	GetAssignedTasks(ctx context.Context, workerID string) ([]jobs.Job, error)
	SubmitTaskResult(ctx context.Context, workerID string, jobID string, taskID string, payload TaskResultPayload) error
}

// TaskResultPayload maps the final execution status reported by a worker.
type TaskResultPayload struct {
	ExitCode int      `json:"exitCode"`
	ErrorLog string   `json:"errorLog,omitempty"`
	Logs     []string `json:"logs"`
}
