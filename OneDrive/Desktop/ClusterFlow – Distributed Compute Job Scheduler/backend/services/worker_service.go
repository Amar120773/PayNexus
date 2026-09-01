package services

import (
	"context"
	"errors"
	"time"
	"clusterflow/jobs"
	"clusterflow/scheduler"
	"clusterflow/telemetry"
	"clusterflow/websocket"
	"clusterflow/workers"

	"go.mongodb.org/mongo-driver/bson"
)

type WorkerService struct {
	repo        workers.WorkerRepository
	jobRepo     jobs.JobRepository
	historyRepo jobs.HistoryRepository
	sched       scheduler.Scheduler
	wsHub       *websocket.Hub
}

func NewWorkerService(
	repo workers.WorkerRepository,
	jobRepo jobs.JobRepository,
	historyRepo jobs.HistoryRepository,
	sched scheduler.Scheduler,
	wsHub *websocket.Hub,
) workers.Service {
	return &WorkerService{
		repo:        repo,
		jobRepo:     jobRepo,
		historyRepo: historyRepo,
		sched:       sched,
		wsHub:       wsHub,
	}
}

func (s *WorkerService) RegisterWorker(ctx context.Context, node *workers.WorkerNode) (*workers.WorkerNode, error) {
	node.State = workers.StateActive
	node.JoinedAt = time.Now().UTC()
	node.LastHeartbeat = time.Now().UTC()

	if err := s.repo.Create(ctx, node); err != nil {
		return nil, err
	}

	telemetry.GlobalLogger.Info("Worker node registered successfully", telemetry.LogFields{
		"workerId": node.ID,
		"hostname": node.Hostname,
		"ip":       node.IPAddress,
		"cores":    node.Resources.CPUCores,
		"memory":   node.Resources.TotalMemoryBytes,
	})

	s.wsHub.Broadcast("worker_registered", node)
	return node, nil
}

func (s *WorkerService) ProcessHeartbeat(ctx context.Context, payload workers.HeartbeatPayload) error {
	// Fetch worker first to verify existence
	_, err := s.repo.FindByID(ctx, payload.WorkerID)
	if err != nil {
		// Auto-register if not found (skeleton convenience)
		newNode := &workers.WorkerNode{
			ID:            payload.WorkerID,
			Hostname:      "auto-registered-node",
			IPAddress:     "0.0.0.0",
			State:         workers.StateActive,
			Resources:     payload.Resources,
			RunningTasks:  payload.RunningTasks,
			JoinedAt:      time.Now().UTC(),
			LastHeartbeat: time.Now().UTC(),
		}
		if _, errReg := s.RegisterWorker(ctx, newNode); errReg != nil {
			return errReg
		}
		return nil
	}

	err = s.repo.UpdateHeartbeat(ctx, payload.WorkerID, payload.Resources, payload.RunningTasks)
	if err != nil {
		return err
	}

	telemetry.GlobalLogger.Info("Worker heartbeat processed", telemetry.LogFields{
		"workerId":     payload.WorkerID,
		"cpuUsage":     payload.Resources.CPUUsagePercent,
		"memoryUsage":  payload.Resources.UsedMemoryBytes,
		"runningTasks": len(payload.RunningTasks),
	})

	s.wsHub.Broadcast("worker_heartbeat", payload)
	return nil
}

func (s *WorkerService) GetActiveWorkers(ctx context.Context) ([]workers.WorkerNode, error) {
	return s.repo.FindAll(ctx)
}

func (s *WorkerService) UpdateWorkerState(ctx context.Context, id string, state workers.WorkerState) error {
	node, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}

	node.State = state
	node.LastHeartbeat = time.Now().UTC()

	if err := s.repo.Update(ctx, node); err != nil {
		return err
	}

	s.wsHub.Broadcast("worker_state_updated", node)
	return nil
}

func (s *WorkerService) CheckOfflineWorkers(ctx context.Context, timeout time.Duration) error {
	list, err := s.repo.FindAll(ctx)
	if err != nil {
		return err
	}

	now := time.Now().UTC()
	for _, node := range list {
		if node.State != workers.StateOffline && now.Sub(node.LastHeartbeat) > timeout {
			node.State = workers.StateOffline
			if err := s.repo.Update(ctx, &node); err == nil {
				telemetry.GlobalLogger.Warn("Worker node marked offline due to heartbeat timeout", telemetry.LogFields{
					"workerId":      node.ID,
					"lastHeartbeat": node.LastHeartbeat.Format(time.RFC3339),
				})
				s.wsHub.Broadcast("worker_went_offline", node)
			}
		}
	}
	return nil
}

// GetAssignedTasks queries the database for any running tasks assigned to a specific worker.
func (s *WorkerService) GetAssignedTasks(ctx context.Context, workerID string) ([]jobs.Job, error) {
	filter := bson.M{
		"state": jobs.StateRunning,
		"tasks": bson.M{
			"$elemMatch": bson.M{
				"assignedNode": workerID,
				"state":        jobs.StateRunning,
			},
		},
	}
	return s.jobRepo.FindAll(ctx, filter)
}

// SubmitTaskResult reports the exit status of a completed task, updates status records, logs histories, and runs retry rules.
func (s *WorkerService) SubmitTaskResult(ctx context.Context, workerID string, jobID string, taskID string, payload workers.TaskResultPayload) error {
	// 1. Fetch Job
	job, err := s.jobRepo.FindByID(ctx, jobID)
	if err != nil {
		return err
	}

	var matchedTask *jobs.Task
	for idx := range job.Tasks {
		if job.Tasks[idx].ID == taskID {
			matchedTask = &job.Tasks[idx]
			break
		}
	}

	if matchedTask == nil {
		return errors.New("task not found in job")
	}

	if matchedTask.AssignedNode != workerID {
		return errors.New("worker ID mismatch for task assignment")
	}

	if matchedTask.State != jobs.StateRunning {
		return errors.New("task is not currently in running state")
	}

	// 2. Log history record
	finishedAt := time.Now().UTC()
	record := &jobs.TaskExecutionRecord{
		JobID:      jobID,
		TaskID:     taskID,
		WorkerID:   workerID,
		Command:    matchedTask.Command,
		State:      jobs.StateSucceeded,
		ExitCode:   payload.ExitCode,
		ErrorLog:   payload.ErrorLog,
		Logs:       payload.Logs,
		StartedAt:  matchedTask.StartedAt,
		FinishedAt: finishedAt,
		DurationMs: finishedAt.Sub(matchedTask.StartedAt).Milliseconds(),
	}

	if payload.ExitCode == 0 {
		matchedTask.State = jobs.StateSucceeded
		matchedTask.FinishedAt = time.Now().UTC()
		matchedTask.ExitCode = 0
		_ = s.jobRepo.Update(ctx, job)
		_ = s.historyRepo.Save(ctx, record)

		telemetry.GlobalLogger.Info("Task executed successfully", telemetry.LogFields{
			"jobId":    jobID,
			"taskId":   taskID,
			"workerId": workerID,
			"duration": record.DurationMs,
		})

		s.wsHub.Broadcast("task_state_updated", map[string]interface{}{
			"jobId":    jobID,
			"taskId":   taskID,
			"state":    jobs.StateSucceeded,
			"exitCode": 0,
		})
	} else {
		record.State = jobs.StateFailed
		// Broadcast failure alert
		_ = s.wsHub.Broadcast("failure_notification", map[string]interface{}{
			"jobId":    jobID,
			"taskId":   taskID,
			"error":    payload.ErrorLog,
			"exitCode": payload.ExitCode,
			"fatal":    matchedTask.Retries >= matchedTask.MaxRetries,
		})

		// Retry check
		if matchedTask.Retries < matchedTask.MaxRetries {
			matchedTask.Retries++
			matchedTask.State = jobs.StatePending
			matchedTask.AssignedNode = ""
			_ = s.jobRepo.Update(ctx, job)
			_ = s.historyRepo.Save(ctx, record)

			telemetry.GlobalLogger.Warn("Task failed, triggering retry", telemetry.LogFields{
				"jobId":    jobID,
				"taskId":   taskID,
				"workerId": workerID,
				"retry":    matchedTask.Retries,
				"error":    payload.ErrorLog,
			})

			s.wsHub.Broadcast("task_state_updated", map[string]interface{}{
				"jobId":    jobID,
				"taskId":   taskID,
				"state":    jobs.StatePending,
				"retry":    matchedTask.Retries,
				"error":    payload.ErrorLog,
			})
		} else {
			matchedTask.State = jobs.StateFailed
			matchedTask.FinishedAt = time.Now().UTC()
			matchedTask.ExitCode = payload.ExitCode
			_ = s.jobRepo.Update(ctx, job)
			_ = s.historyRepo.Save(ctx, record)

			telemetry.GlobalLogger.Error("Task failed completely, max retries reached", telemetry.LogFields{
				"jobId":    jobID,
				"taskId":   taskID,
				"workerId": workerID,
				"exitCode": payload.ExitCode,
				"error":    payload.ErrorLog,
			})

			s.wsHub.Broadcast("task_state_updated", map[string]interface{}{
				"jobId":    jobID,
				"taskId":   taskID,
				"state":    jobs.StateFailed,
				"exitCode": payload.ExitCode,
				"error":    payload.ErrorLog,
			})
		}
	}

	// 3. Trigger scheduling evaluation cycle
	s.sched.TriggerSchedule()
	return nil
}

// GetWorkerByID retrieves a worker node details by its ID.
func (s *WorkerService) GetWorkerByID(ctx context.Context, id string) (*workers.WorkerNode, error) {
	return s.repo.FindByID(ctx, id)
}
