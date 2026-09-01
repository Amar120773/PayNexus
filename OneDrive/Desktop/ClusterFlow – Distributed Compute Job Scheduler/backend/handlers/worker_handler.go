package handlers

import (
	"net/http"
	"clusterflow/workers"

	"github.com/gin-gonic/gin"
)

type WorkerHandler struct {
	service workers.Service
}

func NewWorkerHandler(service workers.Service) *WorkerHandler {
	return &WorkerHandler{service: service}
}

func (h *WorkerHandler) Register(c *gin.Context) {
	var node workers.WorkerNode
	if err := c.ShouldBindJSON(&node); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	registered, err := h.service.RegisterWorker(c.Request.Context(), &node)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, registered)
}

func (h *WorkerHandler) Heartbeat(c *gin.Context) {
	var payload workers.HeartbeatPayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.service.ProcessHeartbeat(c.Request.Context(), payload)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "acknowledged"})
}

func (h *WorkerHandler) List(c *gin.Context) {
	list, err := h.service.GetActiveWorkers(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, list)
}

// GetTasks returns running tasks assigned to a specific worker ID.
func (h *WorkerHandler) GetTasks(c *gin.Context) {
	id := c.Param("id")
	tasksList, err := h.service.GetAssignedTasks(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, tasksList)
}

// SubmitResult handles reporting a task execution completed/failed payload from a worker.
func (h *WorkerHandler) SubmitResult(c *gin.Context) {
	id := c.Param("id")
	taskId := c.Param("taskId")
	jobId := c.Query("jobId")
	if jobId == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "jobId query parameter required"})
		return
	}

	var payload workers.TaskResultPayload
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.service.SubmitTaskResult(c.Request.Context(), id, jobId, taskId, payload)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "result_acknowledged"})
}

// GetByID returns the details of a specific worker node.
func (h *WorkerHandler) GetByID(c *gin.Context) {
	id := c.Param("id")
	node, err := h.service.GetWorkerByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "worker node not found"})
		return
	}
	c.JSON(http.StatusOK, node)
}
