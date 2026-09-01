package middleware

import (
	"time"
	"clusterflow/telemetry"

	"github.com/gin-gonic/gin"
)

// RequestTelemetry records request metrics and logs actions via structured logging.
func RequestTelemetry(log telemetry.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method

		// Process request
		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()
		reqID, _ := c.Get("requestID")

		log.Info("HTTP Request handled", telemetry.LogFields{
			"requestId":  reqID,
			"path":       path,
			"method":     method,
			"status":     status,
			"latencyMs":  latency.Milliseconds(),
			"ip":         c.ClientIP(),
			"userAgent":  c.Request.UserAgent(),
		})

		// Collect metrics here if applicable. Job count incrementation done inside services.
	}
}
