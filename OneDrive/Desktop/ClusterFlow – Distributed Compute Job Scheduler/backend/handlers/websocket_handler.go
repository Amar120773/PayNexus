package handlers

import (
	"net/http"
	"clusterflow/websocket"

	"github.com/gin-gonic/gin"
)

type WebSocketHandler struct {
	hub *websocket.Hub
}

func NewWebSocketHandler(hub *websocket.Hub) *WebSocketHandler {
	return &WebSocketHandler{hub: hub}
}

// Connect upgrades HTTP connection to WebSocket and registers connection to the hub.
func (h *WebSocketHandler) Connect(c *gin.Context) {
	conn, err := h.hub.Upgrade(c.Writer, c.Request)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to upgrade websocket connection"})
		return
	}

	h.hub.RegisterClient(conn)
}
