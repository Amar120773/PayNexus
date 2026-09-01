package jobs

import (
	"context"
	"time"
)

// JobState represents the lifecycle status of a distributed compute job.
type JobState string

const (
	StatePending   JobState = "PENDING"
	StateRunning   JobState = "RUNNING"
	StateSucceeded JobState = "SUCCEEDED"
	StateFailed    JobState = "FAILED"
	StateCancelled JobState = "CANCELLED"
)

// Task represents an individual execution unit within a distributed Job workflow (DAG).
type Task struct {
	ID                 string    `json:"id" bson:"id"`
	Name               string    `json:"name" bson:"name"`
	Command            string    `json:"command" bson:"command"`
	State              JobState  `json:"state" bson:"state"`
	RequiredCores      int       `json:"requiredCores" bson:"requiredCores"`
	RequiredMemory     int64     `json:"requiredMemoryBytes" bson:"requiredMemoryBytes"`
	Retries            int       `json:"retries" bson:"retries"`
	MaxRetries         int       `json:"maxRetries" bson:"maxRetries"`
	DurationSeconds    int       `json:"durationSeconds" bson:"durationSeconds"`
	FailureProbability float64   `json:"failureProbability" bson:"failureProbability"`
	AssignedNode       string    `json:"assignedNode,omitempty" bson:"assignedNode,omitempty"` // Worker ID
	DependsOn          []string  `json:"dependsOn" bson:"dependsOn"`                           // Parent task IDs
	ExitCode           int       `json:"exitCode" bson:"exitCode"`
	StartedAt          time.Time `json:"startedAt,omitempty" bson:"startedAt,omitempty"`
	FinishedAt         time.Time `json:"finishedAt,omitempty" bson:"finishedAt,omitempty"`
}

// Job represents a composite compute request scheduled to run on the cluster.
type Job struct {
	ID          string            `json:"id" bson:"_id,omitempty"`
	Name        string            `json:"name" bson:"name"`
	Description string            `json:"description" bson:"description"`
	CreatorID   string            `json:"creatorId" bson:"creatorId"`
	Priority    int               `json:"priority" bson:"priority"` // High-priority jobs run first
	State       JobState          `json:"state" bson:"state"`
	Tasks       []Task            `json:"tasks" bson:"tasks"`
	Variables   map[string]string `json:"variables" bson:"variables"` // Env variables for execution
	CreatedAt   time.Time         `json:"createdAt" bson:"createdAt"`
	UpdatedAt   time.Time         `json:"updatedAt" bson:"updatedAt"`
	StartedAt   time.Time         `json:"startedAt,omitempty" bson:"startedAt,omitempty"`
	FinishedAt  time.Time         `json:"finishedAt,omitempty" bson:"finishedAt,omitempty"`
}

// JobRepository defines job persistence operations in the data layer.
type JobRepository interface {
	Create(ctx context.Context, job *Job) error
	FindByID(ctx context.Context, id string) (*Job, error)
	FindAll(ctx context.Context, filter map[string]interface{}) ([]Job, error)
	Update(ctx context.Context, job *Job) error
	Delete(ctx context.Context, id string) error
}

// Service defines application use cases for submitting and tracking jobs.
type Service interface {
	SubmitJob(ctx context.Context, job *Job) (*Job, error)
	GetJobByID(ctx context.Context, id string) (*Job, error)
	ListJobs(ctx context.Context, filter map[string]interface{}) ([]Job, error)
	CancelJob(ctx context.Context, id string) error
	RetryJob(ctx context.Context, id string) (*Job, error)
	UpdateJobState(ctx context.Context, id string, state JobState) error
	UpdateTaskState(ctx context.Context, jobId, taskId string, state JobState, exitCode int, assignedNode string) error
}
