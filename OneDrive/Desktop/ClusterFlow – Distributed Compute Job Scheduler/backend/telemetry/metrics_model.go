package telemetry

import (
	"context"
	"time"
)

// MetricSnapshot represents a timeseries database snapshot of cluster performance.
type MetricSnapshot struct {
	ID                 string    `json:"id" bson:"_id,omitempty"`
	Timestamp          time.Time `json:"timestamp" bson:"timestamp"`
	ClusterCPUPercent  float64   `json:"clusterCpuPercent" bson:"clusterCpuPercent"`
	ClusterMemoryBytes int64     `json:"clusterMemoryBytes" bson:"clusterMemoryBytes"`
	ClusterUsedMemory  int64     `json:"clusterUsedMemoryBytes" bson:"clusterUsedMemoryBytes"`
	ActiveJobs         int       `json:"activeJobs" bson:"activeJobs"`
	QueuedJobs         int       `json:"queuedJobs" bson:"queuedJobs"`
	FailedJobs         int       `json:"failedJobs" bson:"failedJobs"`
	Throughput         float64   `json:"throughput" bson:"throughput"`
	OnlineWorkers      int       `json:"onlineWorkers" bson:"onlineWorkers"`
	TotalWorkers       int       `json:"totalWorkers" bson:"totalWorkers"`
}

// MetricsRepository handles persisting cluster metric snapshots.
type MetricsRepository interface {
	Insert(ctx context.Context, metric *MetricSnapshot) error
	GetHistory(ctx context.Context, start, end time.Time) ([]MetricSnapshot, error)
}
