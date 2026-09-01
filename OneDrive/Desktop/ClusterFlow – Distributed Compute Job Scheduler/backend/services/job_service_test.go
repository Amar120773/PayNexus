package services

import (
	"context"
	"errors"
	"testing"

	"clusterflow/jobs"
	"clusterflow/scheduler"
	"clusterflow/websocket"
)

// --- Mocks for Job Service Unit Tests ---

type MockJobRepository struct {
	db map[string]*jobs.Job
}

func (r *MockJobRepository) Create(ctx context.Context, job *jobs.Job) error {
	r.db[job.ID] = job
	return nil
}

func (r *MockJobRepository) FindByID(ctx context.Context, id string) (*jobs.Job, error) {
	j, ok := r.db[id]
	if !ok {
		return nil, errors.New("not found")
	}
	return j, nil
}

func (r *MockJobRepository) FindAll(ctx context.Context, filter map[string]interface{}) ([]jobs.Job, error) {
	var res []jobs.Job
	for _, j := range r.db {
		res = append(res, *j)
	}
	return res, nil
}

func (r *MockJobRepository) Update(ctx context.Context, job *jobs.Job) error {
	r.db[job.ID] = job
	return nil
}

func (r *MockJobRepository) Delete(ctx context.Context, id string) error {
	delete(r.db, id)
	return nil
}

type MockScheduler struct {
	Enqueued map[string]int
	Dequeued []string
}

func (s *MockScheduler) Start(ctx context.Context) error { return nil }
func (s *MockScheduler) Stop() error                  { return nil }
func (s *MockScheduler) TriggerSchedule()             {}
func (s *MockScheduler) EnqueueJob(id string, priority int) error {
	s.Enqueued[id] = priority
	return nil
}
func (s *MockScheduler) DequeueJob(id string) error {
	s.Dequeued = append(s.Dequeued, id)
	return nil
}
func (s *MockScheduler) GetQueueStatus() (int, int, error) { return 0, 0, nil }
func (s *MockScheduler) SetQueuePolicy(p scheduler.QueuePolicy)         {}
func (s *MockScheduler) SetPlacementPolicy(p scheduler.PlacementPolicy) {}

func TestSubmitJob(t *testing.T) {
	repo := &MockJobRepository{db: make(map[string]*jobs.Job)}
	sched := &MockScheduler{Enqueued: make(map[string]int)}
	wsHub := websocket.NewHub(10, 10)

	service := NewJobService(repo, sched, wsHub)

	job := &jobs.Job{
		Name:     "TestJob",
		Priority: 7,
		Tasks: []jobs.Task{
			{ID: "t1", Command: "echo hello"},
		},
	}

	result, err := service.SubmitJob(context.Background(), job)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if result.ID == "" {
		t.Errorf("Expected generated job ID to not be empty")
	}

	if result.State != jobs.StatePending {
		t.Errorf("Expected job state to be PENDING, got %s", result.State)
	}

	if sched.Enqueued[result.ID] != 7 {
		t.Errorf("Expected scheduler to have enqueued job with priority 7")
	}
}

func TestCancelJob(t *testing.T) {
	repo := &MockJobRepository{db: make(map[string]*jobs.Job)}
	sched := &MockScheduler{Enqueued: make(map[string]int)}
	wsHub := websocket.NewHub(10, 10)

	service := NewJobService(repo, sched, wsHub)

	job := &jobs.Job{
		ID:    "job-to-cancel",
		Name:  "TestJob",
		State: jobs.StateRunning,
	}
	_ = repo.Create(context.Background(), job)

	err := service.CancelJob(context.Background(), "job-to-cancel")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	updated, _ := repo.FindByID(context.Background(), "job-to-cancel")
	if updated.State != jobs.StateCancelled {
		t.Errorf("Expected state FAILED/CANCELLED, got %s", updated.State)
	}

	if len(sched.Dequeued) == 0 || sched.Dequeued[0] != "job-to-cancel" {
		t.Errorf("Expected scheduler to dequeue cancelled job")
	}
}

func TestRetryJob(t *testing.T) {
	repo := &MockJobRepository{db: make(map[string]*jobs.Job)}
	sched := &MockScheduler{Enqueued: make(map[string]int)}
	wsHub := websocket.NewHub(10, 10)

	service := NewJobService(repo, sched, wsHub)

	job := &jobs.Job{
		ID:       "job-to-retry",
		State:    jobs.StateFailed,
		Priority: 8,
		Tasks: []jobs.Task{
			{ID: "t1", State: jobs.StateFailed, ExitCode: 1},
		},
	}
	_ = repo.Create(context.Background(), job)

	retried, err := service.RetryJob(context.Background(), "job-to-retry")
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if retried.State != jobs.StatePending {
		t.Errorf("Expected retried job to be PENDING, got %s", retried.State)
	}

	if retried.Tasks[0].State != jobs.StatePending {
		t.Errorf("Expected failed task to be reset to PENDING, got %s", retried.Tasks[0].State)
	}

	if sched.Enqueued["job-to-retry"] != 8 {
		t.Errorf("Expected job to be re-enqueued to scheduler with priority 8")
	}
}
