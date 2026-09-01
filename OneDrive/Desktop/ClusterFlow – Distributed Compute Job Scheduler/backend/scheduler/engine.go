package scheduler

import (
	"context"
	"errors"
	"math/rand"
	"sync"
	"time"

	"clusterflow/jobs"
	"clusterflow/telemetry"
	"clusterflow/websocket"
	"clusterflow/workers"
)

// Engine is the concrete scheduling coordinator implementation.
type Engine struct {
	jobRepo     jobs.JobRepository
	workerRepo  workers.WorkerRepository
	queueRepo   QueueRepository
	historyRepo jobs.HistoryRepository
	wsHub       *websocket.Hub

	queuePolicy     QueuePolicy
	placementPolicy PlacementPolicy

	scheduleCh chan struct{}
	cancelCtx  context.Context
	cancelFunc context.CancelFunc
	mutex      sync.RWMutex
	running    bool
}

// NewSchedulerEngine creates and returns a fully injected scheduling engine coordinator.
func NewSchedulerEngine(
	jobRepo jobs.JobRepository,
	workerRepo workers.WorkerRepository,
	queueRepo QueueRepository,
	historyRepo jobs.HistoryRepository,
	wsHub *websocket.Hub,
) *Engine {
	return &Engine{
		jobRepo:         jobRepo,
		workerRepo:      workerRepo,
		queueRepo:       queueRepo,
		historyRepo:     historyRepo,
		wsHub:           wsHub,
		scheduleCh:      make(chan struct{}, 1),
		queuePolicy:     PriorityQueuePolicy{},
		placementPolicy: LeastLoadedPlacementPolicy{},
	}
}

func (e *Engine) Start(ctx context.Context) error {
	e.mutex.Lock()
	if e.running {
		e.mutex.Unlock()
		return errors.New("scheduler engine is already running")
	}
	e.cancelCtx, e.cancelFunc = context.WithCancel(ctx)
	e.running = true
	e.mutex.Unlock()

	go e.runLoop()
	return nil
}

func (e *Engine) Stop() error {
	e.mutex.Lock()
	defer e.mutex.Unlock()

	if !e.running {
		return nil
	}

	if e.cancelFunc != nil {
		e.cancelFunc()
	}
	e.running = false
	return nil
}

func (e *Engine) TriggerSchedule() {
	select {
	case e.scheduleCh <- struct{}{}:
	default:
		// Queue loop is already triggered or executing evaluations
	}
}

func (e *Engine) EnqueueJob(jobID string, priority int) error {
	item := &PersistentQueueItem{
		JobID:      jobID,
		Priority:   priority,
		Status:     QueueStateWaiting,
		EnqueuedAt: time.Now().UTC(),
	}
	err := e.queueRepo.Enqueue(context.Background(), item)
	if err != nil {
		return err
	}
	telemetry.GlobalLogger.Info("Job enqueued in scheduler", telemetry.LogFields{
		"jobId":    jobID,
		"priority": priority,
	})
	_ = e.wsHub.Broadcast("queue_changed", map[string]interface{}{
		"jobId":    jobID,
		"priority": priority,
		"action":   "enqueue",
	})
	e.TriggerSchedule()
	return nil
}

func (e *Engine) DequeueJob(jobID string) error {
	err := e.queueRepo.Dequeue(context.Background(), jobID)
	if err != nil {
		return err
	}
	_ = e.wsHub.Broadcast("queue_changed", map[string]interface{}{
		"jobId":  jobID,
		"action": "dequeue",
	})
	return nil
}

func (e *Engine) GetQueueStatus() (int, int, error) {
	ctx := context.Background()
	items, err := e.queueRepo.ListWaiting(ctx)
	if err != nil {
		return 0, 0, err
	}

	workerNodes, err := e.workerRepo.FindAll(ctx)
	if err != nil {
		return len(items), 0, err
	}

	activeCount := 0
	for _, node := range workerNodes {
		if node.State == workers.StateActive {
			activeCount++
		}
	}

	return len(items), activeCount, nil
}

func (e *Engine) SetQueuePolicy(policy QueuePolicy) {
	e.mutex.Lock()
	defer e.mutex.Unlock()
	e.queuePolicy = policy
}

func (e *Engine) SetPlacementPolicy(policy PlacementPolicy) {
	e.mutex.Lock()
	defer e.mutex.Unlock()
	e.placementPolicy = policy
}

func (e *Engine) runLoop() {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-e.cancelCtx.Done():
			return
		case <-e.scheduleCh:
			e.evaluateQueue()
		case <-ticker.C:
			e.evaluateQueue()
		}
	}
}

func (e *Engine) evaluateQueue() {
	e.mutex.RLock()
	activeQueuePolicy := e.queuePolicy
	activePlacementPolicy := e.placementPolicy
	e.mutex.RUnlock()

	ctx := context.Background()
	queueItems, err := e.queueRepo.ListWaiting(ctx)
	if err != nil {
		return
	}

	if len(queueItems) == 0 {
		return
	}

	telemetry.GlobalLogger.Info("Scheduler evaluation cycle triggered", telemetry.LogFields{
		"waitingJobsCount": len(queueItems),
	})

	// 1. Sort queue items using the configured Strategy Policy
	activeQueuePolicy.Sort(queueItems)

	// 2. Load all available workers once for optimization in this cycle pass
	workersList, err := e.workerRepo.FindAll(ctx)
	if err != nil {
		return
	}

	// Keep a transient cache of resources allocated in this cycle to prevent race condition overallocations
	transientAllocations := make(map[string]struct {
		cores  int
		memory int64
	})

	for _, item := range queueItems {
		job, err := e.jobRepo.FindByID(ctx, item.JobID)
		if err != nil {
			// Job not found, prune from queue collection
			_ = e.queueRepo.Dequeue(ctx, item.JobID)
			continue
		}

		// Skip evaluating terminal state jobs
		if job.State == jobs.StateSucceeded || job.State == jobs.StateFailed || job.State == jobs.StateCancelled {
			_ = e.queueRepo.Dequeue(ctx, job.ID)
			continue
		}

		jobUpdated := false
		allTasksCompleted := true
		anyTaskFailed := false

		// 3. Evaluate each task in the Job DAG
		for idx := range job.Tasks {
			task := &job.Tasks[idx]

			// Check general states
			if task.State == jobs.StateSucceeded {
				continue
			}
			if task.State == jobs.StateFailed || task.State == jobs.StateCancelled {
				allTasksCompleted = false
				anyTaskFailed = true
				continue
			}

			allTasksCompleted = false

			if task.State == jobs.StateRunning {
				continue
			}

			// 4. Verify Task DAG dependencies
			dependenciesSucceeded := true
			for _, depID := range task.DependsOn {
				depFound := false
				for _, other := range job.Tasks {
					if other.ID == depID {
						depFound = true
						if other.State != jobs.StateSucceeded {
							dependenciesSucceeded = false
						}
						break
					}
				}
				if !depFound || !dependenciesSucceeded {
					dependenciesSucceeded = false
					break
				}
			}

			if !dependenciesSucceeded {
				continue
			}

			// 5. Build dynamic worker list subtracting transient core/memory allocations of this loop cycle
			availableNodes := make([]workers.WorkerNode, 0)
			for _, node := range workersList {
				alloc := transientAllocations[node.ID]
				nodeCopy := node
				nodeCopy.Resources.UsedMemoryBytes += alloc.memory
				// CPU usage simulation adjustments
				usedCores := float64(node.Resources.CPUCores) * (node.Resources.CPUUsagePercent / 100.0)
				simulatedUsedPercent := ((usedCores + float64(alloc.cores)) / float64(node.Resources.CPUCores)) * 100.0
				nodeCopy.Resources.CPUUsagePercent = simulatedUsedPercent
				
				availableNodes = append(availableNodes, nodeCopy)
			}

			// 6. Match worker based on Placement strategy
			targetNode, err := activePlacementPolicy.SelectWorker(*task, availableNodes)
			if err != nil {
				continue // No active worker satisfies resources, skip for next ticker cycle
			}

			// 7. Lock allocation details in transition map
			alloc := transientAllocations[targetNode.ID]
			alloc.cores += task.RequiredCores
			alloc.memory += task.RequiredMemory
			transientAllocations[targetNode.ID] = alloc

			// 8. Update task state to running and dispatch
			task.State = jobs.StateRunning
			task.AssignedNode = targetNode.ID
			task.StartedAt = time.Now().UTC()
			jobUpdated = true

			telemetry.GlobalLogger.Info("Task dispatched successfully", telemetry.LogFields{
				"jobId":      job.ID,
				"taskId":     task.ID,
				"workerId":   targetNode.ID,
				"reqCores":   task.RequiredCores,
				"reqMemory":  task.RequiredMemory,
			})

			// Task is now dispatched. Standalone worker agents will poll and execute this task,
			// reporting results back via the worker REST endpoint.
		}

		// Update parent job values
		if job.State == jobs.StatePending && jobUpdated {
			job.State = jobs.StateRunning
			job.StartedAt = time.Now().UTC()
			job.UpdatedAt = time.Now().UTC()
			_ = e.jobRepo.Update(ctx, job)
			e.wsHub.Broadcast("job_state_updated", job)
		} else if jobUpdated {
			job.UpdatedAt = time.Now().UTC()
			_ = e.jobRepo.Update(ctx, job)
			e.wsHub.Broadcast("job_updated", job)
		}

		// Handle job completion checks
		if allTasksCompleted && !anyTaskFailed {
			job.State = jobs.StateSucceeded
			job.FinishedAt = time.Now().UTC()
			job.UpdatedAt = time.Now().UTC()
			_ = e.jobRepo.Update(ctx, job)
			_ = e.queueRepo.Dequeue(ctx, job.ID)
			telemetry.GlobalLogger.Info("Job completed successfully", telemetry.LogFields{
				"jobId": job.ID,
			})
			e.wsHub.Broadcast("job_state_updated", job)
		} else if anyTaskFailed {
			job.State = jobs.StateFailed
			job.FinishedAt = time.Now().UTC()
			job.UpdatedAt = time.Now().UTC()
			_ = e.jobRepo.Update(ctx, job)
			_ = e.queueRepo.Dequeue(ctx, job.ID)
			telemetry.GlobalLogger.Error("Job execution failed", telemetry.LogFields{
				"jobId": job.ID,
			})
			e.wsHub.Broadcast("job_state_updated", job)
		}
	}
}

// simulateTaskExecution runs a simulation thread executing command details, recording exit codes and retrying on failure.
func (e *Engine) simulateTaskExecution(jobID string, taskID string, taskCopy jobs.Task, workerID string) {
	ctx := context.Background()

	// Simulate latency overhead run (2 to 5 seconds)
	executionDuration := time.Duration(2+rand.Intn(4)) * time.Second
	time.Sleep(executionDuration)

	// Mocking execution success rates
	exitCode := 0
	var errorLog string
	// If command contains 'fail' or random failure rate 10%
	if taskCopy.Command == "fail" || rand.Float64() < 0.15 {
		exitCode = 1
		errorLog = "Execution process exited with status 1: Command failed to resolve"
	}

	// Fetch job to preserve modifications
	job, err := e.jobRepo.FindByID(ctx, jobID)
	if err != nil {
		return
	}

	var matchedTask *jobs.Task
	for idx := range job.Tasks {
		if job.Tasks[idx].ID == taskID {
			matchedTask = &job.Tasks[idx]
			break
		}
	}

	if matchedTask == nil {
		return
	}

	// Save log record in persistent execution histories
	record := &jobs.TaskExecutionRecord{
		JobID:      jobID,
		TaskID:     taskID,
		WorkerID:   workerID,
		Command:    taskCopy.Command,
		ExitCode:   exitCode,
		ErrorLog:   errorLog,
		StartedAt:  matchedTask.StartedAt,
		FinishedAt: time.Now().UTC(),
	}

	if exitCode == 0 {
		matchedTask.State = jobs.StateSucceeded
		matchedTask.FinishedAt = time.Now().UTC()
		matchedTask.ExitCode = 0
		_ = e.jobRepo.Update(ctx, job)
		_ = e.historyRepo.Save(ctx, record)
		e.wsHub.Broadcast("task_state_updated", map[string]interface{}{
			"jobId":    jobID,
			"taskId":   taskID,
			"state":    jobs.StateSucceeded,
			"exitCode": 0,
		})
	} else {
		// Retry check
		if matchedTask.Retries < matchedTask.MaxRetries {
			matchedTask.Retries++
			matchedTask.State = jobs.StatePending
			matchedTask.AssignedNode = ""
			_ = e.jobRepo.Update(ctx, job)
			_ = e.historyRepo.Save(ctx, record)
			e.wsHub.Broadcast("task_state_updated", map[string]interface{}{
				"jobId":    jobID,
				"taskId":   taskID,
				"state":    jobs.StatePending,
				"retry":    matchedTask.Retries,
				"error":    errorLog,
			})
		} else {
			matchedTask.State = jobs.StateFailed
			matchedTask.FinishedAt = time.Now().UTC()
			matchedTask.ExitCode = exitCode
			_ = e.jobRepo.Update(ctx, job)
			_ = e.historyRepo.Save(ctx, record)
			e.wsHub.Broadcast("task_state_updated", map[string]interface{}{
				"jobId":    jobID,
				"taskId":   taskID,
				"state":    jobs.StateFailed,
				"exitCode": exitCode,
				"error":    errorLog,
			})
		}
	}

	// Force scheduler cycle immediately to pick up dependent tasks or update completed job checks
	e.TriggerSchedule()
}
