package scheduler

import (
	"context"
	"time"
)

// QueueStatusState defines the locking state of a job in the queue.
type QueueStatusState string

const (
	QueueStateWaiting   QueueStatusState = "WAITING"
	QueueStateLocked    QueueStatusState = "LOCKED"
	QueueStateDispatched QueueStatusState = "DISPATCHED"
)

// PersistentQueueItem represents a job enqueued in MongoDB, allowing scheduler recovery after restarts.
type PersistentQueueItem struct {
	ID         string           `json:"id" bson:"_id,omitempty"`
	JobID      string           `json:"jobId" bson:"jobId"`
	Priority   int              `json:"priority" bson:"priority"`
	Status     QueueStatusState `json:"status" bson:"status"`
	EnqueuedAt time.Time        `json:"enqueuedAt" bson:"enqueuedAt"`
	LockedBy   string           `json:"lockedBy,omitempty" bson:"lockedBy,omitempty"` // Scheduler engine node ID
	LockedAt   time.Time        `json:"lockedAt,omitempty" bson:"lockedAt,omitempty"`
}

// QueueRepository defines database operations to manage persistent queues.
type QueueRepository interface {
	Enqueue(ctx context.Context, item *PersistentQueueItem) error
	Dequeue(ctx context.Context, jobID string) error
	ListWaiting(ctx context.Context) ([]PersistentQueueItem, error)
	LockNextItem(ctx context.Context, lockerID string) (*PersistentQueueItem, error)
	ReleaseLock(ctx context.Context, jobID string) error
}
