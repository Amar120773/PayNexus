package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/mongo"
)

// HealthHandler manages endpoints for monitoring system viability.
type HealthHandler struct {
	mongoClient *mongo.Client
}

// NewHealthHandler returns a new HealthHandler instance.
func NewHealthHandler(client *mongo.Client) *HealthHandler {
	return &HealthHandler{mongoClient: client}
}

// HealthCheck verifies MongoDB server connectivity and returns overall node viability.
func (h *HealthHandler) HealthCheck(c *gin.Context) {
	status := "OK"
	mongoStatus := "CONNECTED"
	httpStatus := http.StatusOK

	if h.mongoClient == nil {
		status = "DEGRADED"
		mongoStatus = "UNCONFIGURED"
	} else {
		ctx, cancel := context.WithTimeout(c.Request.Context(), 2*time.Second)
		defer cancel()
		if err := h.mongoClient.Ping(ctx, nil); err != nil {
			status = "DEGRADED"
			mongoStatus = "DISCONNECTED: " + err.Error()
			httpStatus = http.StatusServiceUnavailable
		}
	}

	c.JSON(httpStatus, gin.H{
		"status":    status,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"database":  mongoStatus,
		"version":   "1.0.0",
		"service":   "ClusterFlow",
	})
}
