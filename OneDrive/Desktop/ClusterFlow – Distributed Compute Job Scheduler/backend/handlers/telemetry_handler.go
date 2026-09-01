package handlers

import (
	"net/http"
	"time"
	"clusterflow/jobs"
	"clusterflow/telemetry"
	"clusterflow/workers"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson"
)

type TelemetryHandler struct {
	metricsRepo telemetry.MetricsRepository
	jobRepo     jobs.JobRepository
	workerRepo  workers.WorkerRepository
}

// NewTelemetryHandler returns an instance of TelemetryHandler.
func NewTelemetryHandler(
	metricsRepo telemetry.MetricsRepository,
	jobRepo jobs.JobRepository,
	workerRepo workers.WorkerRepository,
) *TelemetryHandler {
	return &TelemetryHandler{
		metricsRepo: metricsRepo,
		jobRepo:     jobRepo,
		workerRepo:  workerRepo,
	}
}

// GetMetrics returns historical cluster telemetry snapshots.
func (h *TelemetryHandler) GetMetrics(c *gin.Context) {
	end := time.Now().UTC()
	start := end.Add(-24 * time.Hour) // default back to 24h

	history, err := h.metricsRepo.GetHistory(c.Request.Context(), start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, history)
}

// GetClusterStatus returns live cluster status metrics including total cores, RAM, and job summaries.
func (h *TelemetryHandler) GetClusterStatus(c *gin.Context) {
	ctx := c.Request.Context()

	workersList, err := h.workerRepo.FindAll(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var activeMemory int64
	var totalMemory int64
	var totalCores int
	var activeCPULoad float64
	var onlineCount int

	for _, w := range workersList {
		totalMemory += w.Resources.TotalMemoryBytes
		totalCores += w.Resources.CPUCores
		if w.State == workers.StateActive {
			onlineCount++
			activeMemory += w.Resources.UsedMemoryBytes
			activeCPULoad += w.Resources.CPUUsagePercent
		}
	}

	avgCPULoad := 0.0
	if onlineCount > 0 {
		avgCPULoad = activeCPULoad / float64(onlineCount)
	}

	pendingJobs, _ := h.jobRepo.FindAll(ctx, bson.M{"state": jobs.StatePending})
	runningJobs, _ := h.jobRepo.FindAll(ctx, bson.M{"state": jobs.StateRunning})
	succeededJobs, _ := h.jobRepo.FindAll(ctx, bson.M{"state": jobs.StateSucceeded})
	failedJobs, _ := h.jobRepo.FindAll(ctx, bson.M{"state": jobs.StateFailed})

	c.JSON(http.StatusOK, gin.H{
		"workers": gin.H{
			"total":  len(workersList),
			"online": onlineCount,
		},
		"resources": gin.H{
			"totalMemoryBytes": totalMemory,
			"usedMemoryBytes":  activeMemory,
			"totalCores":       totalCores,
			"avgCpuLoad":       avgCPULoad,
		},
		"jobs": gin.H{
			"pending":   len(pendingJobs),
			"running":   len(runningJobs),
			"succeeded": len(succeededJobs),
			"failed":    len(failedJobs),
		},
	})
}
