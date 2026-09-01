package handlers

import (
	"net/http"
	"clusterflow/auth"
	"clusterflow/jobs"

	"github.com/gin-gonic/gin"
)

type JobHandler struct {
	service jobs.Service
}

func NewJobHandler(service jobs.Service) *JobHandler {
	return &JobHandler{service: service}
}

func (h *JobHandler) Submit(c *gin.Context) {
	var job jobs.Job
	if err := c.ShouldBindJSON(&job); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Retrieve creator ID from JWT middleware context
	userVal, exists := c.Get("currentUser")
	if exists {
		if u, ok := userVal.(*auth.User); ok {
			job.CreatorID = u.ID
		}
	}

	submitted, err := h.service.SubmitJob(c.Request.Context(), &job)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, submitted)
}

func (h *JobHandler) GetByID(c *gin.Context) {
	id := c.Param("id")
	job, err := h.service.GetJobByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "job not found"})
		return
	}

	c.JSON(http.StatusOK, job)
}

func (h *JobHandler) List(c *gin.Context) {
	filter := make(map[string]interface{})
	state := c.Query("state")
	if state != "" {
		filter["state"] = state
	}

	jobsList, err := h.service.ListJobs(c.Request.Context(), filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, jobsList)
}

func (h *JobHandler) Cancel(c *gin.Context) {
	id := c.Param("id")
	err := h.service.CancelJob(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "cancelled", "jobId": id})
}

// Retry handles resubmitting failed/cancelled DAG tasks of a job.
func (h *JobHandler) Retry(c *gin.Context) {
	id := c.Param("id")
	job, err := h.service.RetryJob(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, job)
}
