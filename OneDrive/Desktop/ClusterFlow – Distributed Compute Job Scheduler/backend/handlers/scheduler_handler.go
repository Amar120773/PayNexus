package handlers

import (
	"net/http"
	"clusterflow/scheduler"

	"github.com/gin-gonic/gin"
)

type SchedulerHandler struct {
	sched     scheduler.Scheduler
	queueRepo scheduler.QueueRepository
}

// NewSchedulerHandler returns an instance of SchedulerHandler.
func NewSchedulerHandler(sched scheduler.Scheduler, queueRepo scheduler.QueueRepository) *SchedulerHandler {
	return &SchedulerHandler{
		sched:     sched,
		queueRepo: queueRepo,
	}
}

// GetQueue returns wait queues and telemetry counts.
func (h *SchedulerHandler) GetQueue(c *gin.Context) {
	ctx := c.Request.Context()
	items, err := h.queueRepo.ListWaiting(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	pending, active, err := h.sched.GetQueueStatus()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"queueItems":         items,
		"pendingJobsCount":   pending,
		"activeWorkersCount": active,
	})
}

// SetPolicy updates scheduler sort or placement policies.
func (h *SchedulerHandler) SetPolicy(c *gin.Context) {
	var payload struct {
		QueuePolicy     string `json:"queuePolicy"`     // FIFO, PRIORITY
		PlacementPolicy string `json:"placementPolicy"` // FIRST_FIT, LEAST_LOADED
	}
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if payload.QueuePolicy != "" {
		switch payload.QueuePolicy {
		case "FIFO":
			h.sched.SetQueuePolicy(scheduler.FIFOQueuePolicy{})
		case "PRIORITY":
			h.sched.SetQueuePolicy(scheduler.PriorityQueuePolicy{})
		default:
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid queuePolicy, choose FIFO or PRIORITY"})
			return
		}
	}

	if payload.PlacementPolicy != "" {
		switch payload.PlacementPolicy {
		case "FIRST_FIT":
			h.sched.SetPlacementPolicy(scheduler.FirstFitPlacementPolicy{})
		case "LEAST_LOADED":
			h.sched.SetPlacementPolicy(scheduler.LeastLoadedPlacementPolicy{})
		default:
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid placementPolicy, choose FIRST_FIT or LEAST_LOADED"})
			return
		}
	}

	c.JSON(http.StatusOK, gin.H{"status": "policies_updated"})
}
