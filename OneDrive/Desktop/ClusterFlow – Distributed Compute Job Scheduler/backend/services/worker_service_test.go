package services

import (
	"context"
	"errors"
	"testing"
	"time"

	"clusterflow/jobs"
	"clusterflow/websocket"
	"clusterflow/workers"
)

// --- Mocks for Worker Service Unit Tests ---

type MockWorkerRepository struct {
	db map[string]*workers.WorkerNode
}

func (r *MockWorkerRepository) Create(ctx context.Context, w *workers.WorkerNode) error {
	r.db[w.ID] = w
	return nil
}

func (r *MockWorkerRepository) FindByID(ctx context.Context, id string) (*workers.WorkerNode, error) {
	w, ok := r.db[id]
	if !ok {
		return nil, errors.New("not found")
	}
	return w, nil
}

func (r *MockWorkerRepository) FindAll(ctx context.Context) ([]workers.WorkerNode, error) {
	var res []workers.WorkerNode
	for _, w := range r.db {
		res = append(res, *w)
	}
	return res, nil
}

func (r *MockWorkerRepository) Update(ctx context.Context, w *workers.WorkerNode) error {
	r.db[w.ID] = w
	return nil
}

func (r *MockWorkerRepository) Delete(ctx context.Context, id string) error {
	delete(r.db, id)
	return nil
}

func (r *MockWorkerRepository) UpdateHeartbeat(ctx context.Context, id string, stats workers.ResourceStats, running []string) error {
	w, ok := r.db[id]
	if !ok {
		return errors.New("not found")
	}
	w.Resources = stats
	w.RunningTasks = running
	w.LastHeartbeat = time.Now().UTC()
	return nil
}

type MockHistoryRepository struct {
	records []jobs.TaskExecutionRecord
}

func (r *MockHistoryRepository) Save(ctx context.Context, record *jobs.TaskExecutionRecord) error {
	r.records = append(r.records, *record)
	return nil
}

func (r *MockHistoryRepository) GetByJob(ctx context.Context, jobID string) ([]jobs.TaskExecutionRecord, error) {
	return nil, nil
}

func (r *MockHistoryRepository) GetByWorker(ctx context.Context, workerID string) ([]jobs.TaskExecutionRecord, error) {
	return nil, nil
}

func TestRegisterAndHeartbeat(t *testing.T) {
	wRepo := &MockWorkerRepository{db: make(map[string]*workers.WorkerNode)}
	jRepo := &MockJobRepository{db: make(map[string]*jobs.Job)}
	hRepo := &MockHistoryRepository{records: make([]jobs.TaskExecutionRecord, 0)}
	sched := &MockScheduler{}
	wsHub := websocket.NewHub(10, 10)

	service := NewWorkerService(wRepo, jRepo, hRepo, sched, wsHub)

	// 1. Test Node Registration
	node := &workers.WorkerNode{
		ID:       "node-1",
		Hostname: "test-host",
		Resources: workers.ResourceStats{
			CPUCores: 8,
		},
	}

	registered, err := service.RegisterWorker(context.Background(), node)
	if err != nil {
		t.Fatalf("Unexpected registration error: %v", err)
	}

	if registered.State != workers.StateActive {
		t.Errorf("Expected active state, got %s", registered.State)
	}

	// 2. Test Heartbeat Update
	payload := workers.HeartbeatPayload{
		WorkerID: "node-1",
		Resources: workers.ResourceStats{
			CPUCores:         8,
			CPUUsagePercent:  45.0,
			TotalMemoryBytes: 16 * 1024 * 1024 * 1024,
			UsedMemoryBytes:  8 * 1024 * 1024 * 1024,
		},
		RunningTasks: []string{"t1"},
	}

	err = service.ProcessHeartbeat(context.Background(), payload)
	if err != nil {
		t.Fatalf("Unexpected heartbeat error: %v", err)
	}

	updated, _ := wRepo.FindByID(context.Background(), "node-1")
	if updated.Resources.CPUUsagePercent != 45.0 {
		t.Errorf("Expected heartbeat CPU usage 45%%, got %.1f", updated.Resources.CPUUsagePercent)
	}
}

func TestCheckOfflineWorkers(t *testing.T) {
	wRepo := &MockWorkerRepository{db: make(map[string]*workers.WorkerNode)}
	jRepo := &MockJobRepository{db: make(map[string]*jobs.Job)}
	hRepo := &MockHistoryRepository{records: make([]jobs.TaskExecutionRecord, 0)}
	sched := &MockScheduler{}
	wsHub := websocket.NewHub(10, 10)

	service := NewWorkerService(wRepo, jRepo, hRepo, sched, wsHub)

	node1 := &workers.WorkerNode{
		ID:            "node-active",
		State:         workers.StateActive,
		LastHeartbeat: time.Now().UTC(),
	}
	node2 := &workers.WorkerNode{
		ID:            "node-expired",
		State:         workers.StateActive,
		LastHeartbeat: time.Now().UTC().Add(-30 * time.Second),
	}

	_ = wRepo.Create(context.Background(), node1)
	_ = wRepo.Create(context.Background(), node2)

	// Check with a timeout threshold of 10 seconds
	err := service.CheckOfflineWorkers(context.Background(), 10*time.Second)
	if err != nil {
		t.Fatalf("Unexpected scanning error: %v", err)
	}

	res1, _ := wRepo.FindByID(context.Background(), "node-active")
	res2, _ := wRepo.FindByID(context.Background(), "node-expired")

	if res1.State != workers.StateActive {
		t.Errorf("Expected node-active to remain active")
	}

	if res2.State != workers.StateOffline {
		t.Errorf("Expected node-expired to be marked offline, got %s", res2.State)
	}
}

func TestSubmitTaskResultSuccess(t *testing.T) {
	wRepo := &MockWorkerRepository{db: make(map[string]*workers.WorkerNode)}
	jRepo := &MockJobRepository{db: make(map[string]*jobs.Job)}
	hRepo := &MockHistoryRepository{records: make([]jobs.TaskExecutionRecord, 0)}
	sched := &MockScheduler{}
	wsHub := websocket.NewHub(10, 10)

	service := NewWorkerService(wRepo, jRepo, hRepo, sched, wsHub)

	job := &jobs.Job{
		ID: "job-1",
		Tasks: []jobs.Task{
			{ID: "t1", State: jobs.StateRunning, AssignedNode: "worker-1", Command: "echo success"},
		},
	}
	_ = jRepo.Create(context.Background(), job)

	payload := workers.TaskResultPayload{
		ExitCode: 0,
		Logs:     []string{"All steps succeeded"},
	}

	err := service.SubmitTaskResult(context.Background(), "worker-1", "job-1", "t1", payload)
	if err != nil {
		t.Fatalf("Unexpected task result error: %v", err)
	}

	updatedJob, _ := jRepo.FindByID(context.Background(), "job-1")
	if updatedJob.Tasks[0].State != jobs.StateSucceeded {
		t.Errorf("Expected task state to be SUCCEEDED, got %s", updatedJob.Tasks[0].State)
	}

	if len(hRepo.records) == 0 || hRepo.records[0].ExitCode != 0 {
		t.Errorf("Expected task history record with exit code 0 to be saved")
	}
}
