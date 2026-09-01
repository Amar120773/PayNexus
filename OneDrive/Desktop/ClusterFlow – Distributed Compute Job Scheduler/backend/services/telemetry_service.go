package services

import (
	"context"
	"time"

	"clusterflow/jobs"
	"clusterflow/scheduler"
	"clusterflow/telemetry"
	"clusterflow/websocket"
	"clusterflow/workers"

	"go.mongodb.org/mongo-driver/bson"
)

// TelemetryService aggregates performance metrics across jobs, workers, queues and histories.
type TelemetryService struct {
	metricsRepo telemetry.MetricsRepository
	jobRepo     jobs.JobRepository
	workerRepo  workers.WorkerRepository
	queueRepo   scheduler.QueueRepository
	historyRepo jobs.HistoryRepository
	wsHub       *websocket.Hub
}

// NewTelemetryService creates and returns a fully injected telemetry monitoring service.
func NewTelemetryService(
	metricsRepo telemetry.MetricsRepository,
	jobRepo jobs.JobRepository,
	workerRepo workers.WorkerRepository,
	queueRepo scheduler.QueueRepository,
	historyRepo jobs.HistoryRepository,
	wsHub *websocket.Hub,
) *TelemetryService {
	return &TelemetryService{
		metricsRepo: metricsRepo,
		jobRepo:     jobRepo,
		workerRepo:  workerRepo,
		queueRepo:   queueRepo,
		historyRepo: historyRepo,
		wsHub:       wsHub,
	}
}

// Start initiates a background daemon gathering and persisting metrics snapshots every 5 seconds.
func (s *TelemetryService) Start(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Second)
	go func() {
		for {
			select {
			case <-ctx.Done():
				ticker.Stop()
				return
			case <-ticker.C:
				s.collectAndPersist(ctx)
			}
		}
	}()
}

func (s *TelemetryService) collectAndPersist(ctx context.Context) {
	// 1. Fetch Workers for capacity calculations
	workersList, err := s.workerRepo.FindAll(ctx)
	if err != nil {
		return
	}

	var totalMemory int64
	var usedMemory int64
	var totalCPUUsage float64
	var onlineWorkers int

	for _, node := range workersList {
		if node.State == workers.StateActive {
			onlineWorkers++
			totalCPUUsage += node.Resources.CPUUsagePercent
			totalMemory += node.Resources.TotalMemoryBytes
			usedMemory += node.Resources.UsedMemoryBytes
		}
	}

	avgCPU := 0.0
	if onlineWorkers > 0 {
		avgCPU = totalCPUUsage / float64(onlineWorkers)
	}

	// 2. Fetch Queued jobs size
	queueItems, _ := s.queueRepo.ListWaiting(ctx)
	queuedCount := len(queueItems)

	// 3. Fetch Active running jobs count
	runningJobsList, _ := s.jobRepo.FindAll(ctx, bson.M{"state": jobs.StateRunning})
	activeCount := len(runningJobsList)

	// 4. Fetch Failed jobs count
	failedJobsList, _ := s.jobRepo.FindAll(ctx, bson.M{"state": jobs.StateFailed})
	failedCount := len(failedJobsList)

	// 5. Calculate Job Throughput: completed jobs in last 5 minutes (rate per minute)
	finishedJobsList, _ := s.jobRepo.FindAll(ctx, bson.M{
		"state": jobs.StateSucceeded,
		"finishedAt": bson.M{
			"$gte": time.Now().UTC().Add(-5 * time.Minute),
		},
	})
	throughputVal := float64(len(finishedJobsList)) / 5.0

	// 6. Persist Timeseries Snapshot
	snapshot := &telemetry.MetricSnapshot{
		Timestamp:          time.Now().UTC(),
		ClusterCPUPercent:  avgCPU,
		ClusterMemoryBytes: totalMemory,
		ClusterUsedMemory:  usedMemory,
		ActiveJobs:         activeCount,
		QueuedJobs:         queuedCount,
		FailedJobs:         failedCount,
		Throughput:         throughputVal,
		OnlineWorkers:      onlineWorkers,
		TotalWorkers:       len(workersList),
	}

	_ = s.metricsRepo.Insert(ctx, snapshot)
	_ = s.wsHub.Broadcast("metrics_updated", snapshot)

	// 7. Sync variables to master Prometheus gauges for scraping
	promMetrics := telemetry.GetMetrics()
	promMetrics.ActiveWorkers.Set(float64(onlineWorkers))
	promMetrics.TasksRunning.Set(float64(activeCount))

	telemetry.GlobalLogger.Info("Cluster telemetry metrics snapshot", telemetry.LogFields{
		"onlineWorkers": onlineWorkers,
		"totalWorkers":  len(workersList),
		"cpuUsage":      avgCPU,
		"memoryUsed":    usedMemory,
		"activeJobs":    activeCount,
		"queuedJobs":    queuedCount,
		"failedJobs":    failedCount,
		"throughput":    throughputVal,
	})
}
