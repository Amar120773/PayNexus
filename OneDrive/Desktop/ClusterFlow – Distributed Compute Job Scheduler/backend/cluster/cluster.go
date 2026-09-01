package cluster

import (
	"context"
	"time"
)

// ClusterStatus represents the aggregate operating health of the compute cluster.
type ClusterStatus string

const (
	StatusHealthy  ClusterStatus = "HEALTHY"
	StatusDegraded ClusterStatus = "DEGRADED"
	StatusCritical ClusterStatus = "CRITICAL"
)

// Cluster represents the metadata and state snapshot of the entire distributed scheduler environment.
type Cluster struct {
	ID           string        `json:"id" bson:"_id,omitempty"`
	Name         string        `json:"name" bson:"name"`
	Status       ClusterStatus `json:"status" bson:"status"`
	ActiveNodes  int           `json:"activeNodes" bson:"activeNodes"`
	TotalCores   int           `json:"totalCores" bson:"totalCores"`
	TotalMemory  int64         `json:"totalMemoryBytes" bson:"totalMemoryBytes"`
	TotalDisk    int64         `json:"totalDiskBytes" bson:"totalDiskBytes"`
	Version      string        `json:"version" bson:"version"`
	UpdatedAt    time.Time     `json:"updatedAt" bson:"updatedAt"`
}

// Repository defines DB persistence methods for saving cluster configuration states.
type Repository interface {
	Get(ctx context.Context, id string) (*Cluster, error)
	Update(ctx context.Context, cluster *Cluster) error
}
