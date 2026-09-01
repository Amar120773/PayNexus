package services

import (
	"context"
	"errors"
	"time"
	"clusterflow/jobs"
	"clusterflow/scheduler"
	"clusterflow/telemetry"
	"clusterflow/websocket"
)

type JobService struct {
	repo      jobs.JobRepository
	sched     scheduler.Scheduler
	wsHub     *websocket.Hub
}

func NewJobService(repo jobs.JobRepository, sched scheduler.Scheduler, wsHub *websocket.Hub) jobs.Service {
	return &JobService{
		repo:  repo,
		sched: sched,
		wsHub: wsHub,
	}
}

func (s *JobService) SubmitJob(ctx context.Context, job *jobs.Job) (*jobs.Job, error) {
	job.ID = time.Now().Format("20060102150405-") + job.Name // Simple ID generation skeleton
	job.State = jobs.StatePending
	job.CreatedAt = time.Now().UTC()
	job.UpdatedAt = time.Now().UTC()

	// Initialize individual tasks status
	for i := range job.Tasks {
		job.Tasks[i].State = jobs.StatePending
	}

	if err := s.repo.Create(ctx, job); err != nil {
		return nil, err
	}

	// Submit Job to scheduling queue
	if err := s.sched.EnqueueJob(job.ID, job.Priority); err != nil {
		return nil, err
	}

	telemetry.GlobalLogger.Info("Job submitted successfully", telemetry.LogFields{
		"jobId":      job.ID,
		"name":       job.Name,
		"priority":   job.Priority,
		"tasksCount": len(job.Tasks),
	})

	s.wsHub.Broadcast("job_submitted", job)

	return job, nil
}

func (s *JobService) GetJobByID(ctx context.Context, id string) (*jobs.Job, error) {
	return s.repo.FindByID(ctx, id)
}

func (s *JobService) ListJobs(ctx context.Context, filter map[string]interface{}) ([]jobs.Job, error) {
	return s.repo.FindAll(ctx, filter)
}

func (s *JobService) CancelJob(ctx context.Context, id string) error {
	job, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}

	job.State = jobs.StateCancelled
	job.FinishedAt = time.Now().UTC()
	job.UpdatedAt = time.Now().UTC()

	if err := s.repo.Update(ctx, job); err != nil {
		return err
	}

	// Dequeue from scheduling engine
	_ = s.sched.DequeueJob(job.ID)

	telemetry.GlobalLogger.Info("Job cancelled successfully", telemetry.LogFields{
		"jobId": job.ID,
	})

	s.wsHub.Broadcast("job_cancelled", job)

	return nil
}

func (s *JobService) UpdateJobState(ctx context.Context, id string, state jobs.JobState) error {
	job, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}

	job.State = state
	job.UpdatedAt = time.Now().UTC()
	switch state {
	case jobs.StateRunning:
		job.StartedAt = time.Now().UTC()
	case jobs.StateSucceeded, jobs.StateFailed, jobs.StateCancelled:
		job.FinishedAt = time.Now().UTC()
	}

	if err := s.repo.Update(ctx, job); err != nil {
		return err
	}

	telemetry.GlobalLogger.Info("Job state updated", telemetry.LogFields{
		"jobId": job.ID,
		"state": string(state),
	})

	s.wsHub.Broadcast("job_state_updated", job)
	return nil
}

func (s *JobService) UpdateTaskState(ctx context.Context, jobId, taskId string, state jobs.JobState, exitCode int, assignedNode string) error {
	job, err := s.repo.FindByID(ctx, jobId)
	if err != nil {
		return err
	}

	taskFound := false
	for i, task := range job.Tasks {
		if task.ID == taskId {
			job.Tasks[i].State = state
			job.Tasks[i].ExitCode = exitCode
			job.Tasks[i].AssignedNode = assignedNode
			switch state {
			case jobs.StateRunning:
				job.Tasks[i].StartedAt = time.Now().UTC()
			case jobs.StateSucceeded, jobs.StateFailed:
				job.Tasks[i].FinishedAt = time.Now().UTC()
			}
			taskFound = true
			break
		}
	}

	if !taskFound {
		return errors.New("task not found in job")
	}

	job.UpdatedAt = time.Now().UTC()
	if err := s.repo.Update(ctx, job); err != nil {
		return err
	}

	telemetry.GlobalLogger.Info("Task state updated", telemetry.LogFields{
		"jobId":        jobId,
		"taskId":       taskId,
		"state":        string(state),
		"exitCode":     exitCode,
		"assignedNode": assignedNode,
	})

	s.wsHub.Broadcast("task_state_updated", map[string]interface{}{
		"jobId":        jobId,
		"taskId":       taskId,
		"state":        state,
		"exitCode":     exitCode,
		"assignedNode": assignedNode,
	})

	return nil
}

// RetryJob restarts failed or cancelled tasks in a job and submits it back to the scheduling loop.
func (s *JobService) RetryJob(ctx context.Context, id string) (*jobs.Job, error) {
	job, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}

	if job.State != jobs.StateFailed && job.State != jobs.StateCancelled {
		return nil, errors.New("only failed or cancelled jobs can be retried")
	}

	// Reset state of failed or cancelled tasks back to PENDING
	for i := range job.Tasks {
		if job.Tasks[i].State == jobs.StateFailed || job.Tasks[i].State == jobs.StateCancelled {
			job.Tasks[i].State = jobs.StatePending
			job.Tasks[i].ExitCode = 0
			job.Tasks[i].AssignedNode = ""
			job.Tasks[i].Retries = 0
		}
	}

	job.State = jobs.StatePending
	job.FinishedAt = time.Time{}
	job.UpdatedAt = time.Now().UTC()

	if err := s.repo.Update(ctx, job); err != nil {
		return nil, err
	}

	// Re-enqueue into scheduling queue
	if err := s.sched.EnqueueJob(job.ID, job.Priority); err != nil {
		return nil, err
	}

	telemetry.GlobalLogger.Info("Job retry triggered successfully", telemetry.LogFields{
		"jobId": job.ID,
	})

	s.wsHub.Broadcast("job_state_updated", job)
	return job, nil
}
