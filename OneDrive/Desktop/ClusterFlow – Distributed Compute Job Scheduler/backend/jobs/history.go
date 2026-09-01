package jobs

import (
	"context"
	"time"
)

// TaskExecutionRecord stores details of an individual task execution event.
type TaskExecutionRecord struct {
	ID         string    `json:"id" bson:"_id,omitempty"`
	JobID      string    `json:"jobId" bson:"jobId"`
	TaskID     string    `json:"taskId" bson:"taskId"`
	WorkerID   string    `json:"workerId" bson:"workerId"`
	Command    string    `json:"command" bson:"command"`
	State      JobState  `json:"state" bson:"state"`
	ExitCode   int       `json:"exitCode" bson:"exitCode"`
	ErrorLog   string    `json:"errorLog,omitempty" bson:"errorLog,omitempty"`
	Logs       []string  `json:"logs" bson:"logs"`
	StartedAt  time.Time `json:"startedAt" bson:"startedAt"`
	FinishedAt time.Time `json:"finishedAt" bson:"finishedAt"`
	DurationMs int64     `json:"durationMs" bson:"durationMs"`
}

// HistoryRepository manages saving and querying task execution logs.
type HistoryRepository interface {
	Save(ctx context.Context, record *TaskExecutionRecord) error
	GetByJob(ctx context.Context, jobID string) ([]TaskExecutionRecord, error)
	GetByWorker(ctx context.Context, workerID string) ([]TaskExecutionRecord, error)
}
