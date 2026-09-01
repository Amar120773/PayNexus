package handlers

import (
	"net/http"
	"clusterflow/auth"
	"clusterflow/telemetry"

	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	service auth.Service
}

func NewAuthHandler(service auth.Service) *AuthHandler {
	return &AuthHandler{service: service}
}

func (h *AuthHandler) Register(c *gin.Context) {
	var creds auth.Credentials
	if err := c.ShouldBindJSON(&creds); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	response, err := h.service.Register(c.Request.Context(), creds)
	if err != nil {
		telemetry.GlobalLogger.Warn("User registration failed", telemetry.LogFields{
			"email": creds.Email,
			"error": err.Error(),
		})
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	telemetry.GlobalLogger.Info("User registered successfully", telemetry.LogFields{
		"email": creds.Email,
	})
	c.JSON(http.StatusCreated, response)
}

func (h *AuthHandler) Login(c *gin.Context) {
	var creds auth.Credentials
	if err := c.ShouldBindJSON(&creds); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	response, err := h.service.Login(c.Request.Context(), creds)
	if err != nil {
		telemetry.GlobalLogger.Warn("User login failed", telemetry.LogFields{
			"email": creds.Email,
			"error": err.Error(),
		})
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	telemetry.GlobalLogger.Info("User logged in successfully", telemetry.LogFields{
		"email": creds.Email,
	})
	c.JSON(http.StatusOK, response)
}
