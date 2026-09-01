package scheduler

import (
	"context"
	"testing"
	"time"

	"clusterflow/jobs"
	"clusterflow/workers"
)

func TestFIFOQueuePolicy(t *testing.T) {
	policy := FIFOQueuePolicy{}
	now := time.Now()

	items := []PersistentQueueItem{
		{JobID: "job-1", Priority: 5, EnqueuedAt: now.Add(10 * time.Second)},
		{JobID: "job-2", Priority: 9, EnqueuedAt: now},
		{JobID: "job-3", Priority: 2, EnqueuedAt: now.Add(5 * time.Second)},
	}

	policy.Sort(items)

	if items[0].JobID != "job-2" {
		t.Errorf("Expected first item to be job-2, got %s", items[0].JobID)
	}
	if items[1].JobID != "job-3" {
		t.Errorf("Expected second item to be job-3, got %s", items[1].JobID)
	}
	if items[2].JobID != "job-1" {
		t.Errorf("Expected third item to be job-1, got %s", items[2].JobID)
	}
}

func TestPriorityQueuePolicy(t *testing.T) {
	policy := PriorityQueuePolicy{}
	now := time.Now()

	items := []PersistentQueueItem{
		{JobID: "job-1", Priority: 5, EnqueuedAt: now},
		{JobID: "job-2", Priority: 9, EnqueuedAt: now.Add(5 * time.Second)},
		{JobID: "job-3", Priority: 5, EnqueuedAt: now.Add(-5 * time.Second)},
	}

	policy.Sort(items)

	if items[0].JobID != "job-2" {
		t.Errorf("Expected highest priority job-2, got %s", items[0].JobID)
	}
	// job-3 has same priority as job-1 but was enqueued earlier (Add(-5s))
	if items[1].JobID != "job-3" {
		t.Errorf("Expected older enqueued job-3 next, got %s", items[1].JobID)
	}
	if items[2].JobID != "job-1" {
		t.Errorf("Expected job-1 last, got %s", items[2].JobID)
	}
}

func TestFirstFitPlacementPolicy(t *testing.T) {
	policy := FirstFitPlacementPolicy{}

	task := jobs.Task{
		RequiredCores:  4,
		RequiredMemory: 8 * 1024 * 1024 * 1024,
	}

	nodes := []workers.WorkerNode{
		{
			ID:    "node-1",
			State: workers.StateActive,
			Resources: workers.ResourceStats{
				CPUCores:         8,
				CPUUsagePercent:  80.0, // 20% free core capacity (1.6 cores free)
				TotalMemoryBytes: 16 * 1024 * 1024 * 1024,
				UsedMemoryBytes:  12 * 1024 * 1024 * 1024, // 4GB memory free (Not enough for 8GB task!)
			},
		},
		{
			ID:    "node-2",
			State: workers.StateActive,
			Resources: workers.ResourceStats{
				CPUCores:         8,
				CPUUsagePercent:  10.0, // 90% free core capacity (7.2 cores free)
				TotalMemoryBytes: 16 * 1024 * 1024 * 1024,
				UsedMemoryBytes:  4 * 1024 * 1024 * 1024, // 12GB memory free (Enough!)
			},
		},
	}

	selected, err := policy.SelectWorker(task, nodes)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if selected.ID != "node-2" {
		t.Errorf("Expected node-2 to be selected, got %s", selected.ID)
	}
}

func TestLeastLoadedPlacementPolicy(t *testing.T) {
	policy := LeastLoadedPlacementPolicy{}

	task := jobs.Task{
		RequiredCores:  2,
		RequiredMemory: 2 * 1024 * 1024 * 1024,
	}

	nodes := []workers.WorkerNode{
		{
			ID:    "node-1",
			State: workers.StateActive,
			Resources: workers.ResourceStats{
				CPUCores:         8,
				CPUUsagePercent:  50.0, // 4 cores free, CPUUsage 50%
				TotalMemoryBytes: 16 * 1024 * 1024 * 1024,
				UsedMemoryBytes:  4 * 1024 * 1024 * 1024,
			},
		},
		{
			ID:    "node-2",
			State: workers.StateActive,
			Resources: workers.ResourceStats{
				CPUCores:         8,
				CPUUsagePercent:  20.0, // 6.4 cores free, CPUUsage 20% (Least loaded!)
				TotalMemoryBytes: 16 * 1024 * 1024 * 1024,
				UsedMemoryBytes:  4 * 1024 * 1024 * 1024,
			},
		},
		{
			ID:    "node-3",
			State: workers.StateOffline, // Offline node, must be skipped!
			Resources: workers.ResourceStats{
				CPUCores:         8,
				CPUUsagePercent:  10.0,
				TotalMemoryBytes: 16 * 1024 * 1024 * 1024,
				UsedMemoryBytes:  1 * 1024 * 1024 * 1024,
			},
		},
	}

	selected, err := policy.SelectWorker(task, nodes)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if selected.ID != "node-2" {
		t.Errorf("Expected node-2 to be selected, got %s", selected.ID)
	}
}

// Mock Engine Context test skeleton
func TestSchedulerEngineMock(t *testing.T) {
	ctx := context.Background()
	if ctx == nil {
		t.Errorf("Expected context to not be nil")
	}
}
