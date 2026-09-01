package scheduler

import (
	"context"
	"errors"
	"sort"
	"clusterflow/jobs"
	"clusterflow/workers"
)

// QueueItem represents a item queued in the scheduler priority queue.
type QueueItem struct {
	JobID    string `json:"jobId"`
	Priority int    `json:"priority"`
}

// QueuePolicy defines the interface to sort queued jobs.
type QueuePolicy interface {
	Name() string
	Sort(items []PersistentQueueItem)
}

// PlacementPolicy defines the interface to select the best worker node for a task.
type PlacementPolicy interface {
	Name() string
	SelectWorker(task jobs.Task, nodes []workers.WorkerNode) (*workers.WorkerNode, error)
}

// --- Default Queue Policies ---

// FIFOQueuePolicy sorts items purely by enqueued time.
type FIFOQueuePolicy struct{}

func (p FIFOQueuePolicy) Name() string { return "FIFO" }
func (p FIFOQueuePolicy) Sort(items []PersistentQueueItem) {
	sort.Slice(items, func(i, j int) bool {
		return items[i].EnqueuedAt.Before(items[j].EnqueuedAt)
	})
}

// PriorityQueuePolicy sorts items by priority descending, then enqueued time ascending.
type PriorityQueuePolicy struct{}

func (p PriorityQueuePolicy) Name() string { return "PRIORITY" }
func (p PriorityQueuePolicy) Sort(items []PersistentQueueItem) {
	sort.Slice(items, func(i, j int) bool {
		if items[i].Priority != items[j].Priority {
			return items[i].Priority > items[j].Priority
		}
		return items[i].EnqueuedAt.Before(items[j].EnqueuedAt)
	})
}

// --- Default Placement Policies ---

// FirstFitPlacementPolicy selects the first active worker with enough resources.
type FirstFitPlacementPolicy struct{}

func (p FirstFitPlacementPolicy) Name() string { return "FIRST_FIT" }
func (p FirstFitPlacementPolicy) SelectWorker(task jobs.Task, nodes []workers.WorkerNode) (*workers.WorkerNode, error) {
	for i := range nodes {
		node := &nodes[i]
		if node.State == workers.StateActive &&
			node.FreeCores() >= task.RequiredCores &&
			node.FreeMemory() >= task.RequiredMemory {
			return node, nil
		}
	}
	return nil, errors.New("no suitable worker node found with available capacity")
}

// LeastLoadedPlacementPolicy selects the worker with the lowest CPU load percentage.
type LeastLoadedPlacementPolicy struct{}

func (p LeastLoadedPlacementPolicy) Name() string { return "LEAST_LOADED" }
func (p LeastLoadedPlacementPolicy) SelectWorker(task jobs.Task, nodes []workers.WorkerNode) (*workers.WorkerNode, error) {
	var bestNode *workers.WorkerNode
	minLoad := 101.0 // CPU Load percentage is max 100

	for i := range nodes {
		node := &nodes[i]
		if node.State == workers.StateActive &&
			node.FreeCores() >= task.RequiredCores &&
			node.FreeMemory() >= task.RequiredMemory {
			if node.Resources.CPUUsagePercent < minLoad {
				minLoad = node.Resources.CPUUsagePercent
				bestNode = node
			}
		}
	}

	if bestNode == nil {
		return nil, errors.New("no suitable worker node found with available capacity")
	}
	return bestNode, nil
}

// Scheduler defines the loop-based engine responsible for matching pending tasks to active worker resource capacities.
type Scheduler interface {
	Start(ctx context.Context) error
	Stop() error
	TriggerSchedule()
	EnqueueJob(jobID string, priority int) error
	DequeueJob(jobID string) error
	GetQueueStatus() (pendingJobsCount int, activeWorkersCount int, err error)
	// Dynamic Policy Setters
	SetQueuePolicy(policy QueuePolicy)
	SetPlacementPolicy(policy PlacementPolicy)
}

// TaskScheduler holds custom logic algorithms to determine where a Task is placed.
type TaskScheduler interface {
	ScheduleTask(ctx context.Context, taskID string, requiredCores int, requiredMemory int64) (string, error)
}
