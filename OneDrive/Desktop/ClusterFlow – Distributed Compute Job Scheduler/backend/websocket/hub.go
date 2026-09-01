package websocket

import (
	"encoding/json"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
)

// Message defines the standard JSON payload streamed over websocket connections.
type Message struct {
	Event   string          `json:"event"`   // e.g., "job_updated", "worker_heartbeat", "stats_summary"
	Payload json.RawMessage `json:"payload"` // Nested event data
}

// Client represents a connected user terminal session.
type Client struct {
	Hub  *Hub
	Conn *websocket.Conn
	Send chan Message
}

// Hub maintains the set of active clients and handles broadcasting messages to them.
type Hub struct {
	clients    map[*Client]bool
	broadcast  chan Message
	register   chan *Client
	unregister chan *Client
	mutex      sync.RWMutex
	upgrader   websocket.Upgrader
}

// NewHub creates and returns a WebSocket Broadcast Hub instance.
func NewHub(readBufSize, writeBufSize int) *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan Message),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  readBufSize,
			WriteBufferSize: writeBufSize,
			CheckOrigin: func(r *http.Request) bool {
				// Allow all origins for production-configured CORS verification in middleware
				return true
			},
		},
	}
}

// Run starts the WebSocket hub event dispatch loop.
func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mutex.Lock()
			h.clients[client] = true
			h.mutex.Unlock()

		case client := <-h.unregister:
			h.mutex.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.Send)
			}
			h.mutex.Unlock()

		case message := <-h.broadcast:
			h.mutex.RLock()
			for client := range h.clients {
				select {
				case client.Send <- message:
				default:
					h.mutex.RUnlock()
					h.mutex.Lock()
					if _, ok := h.clients[client]; ok {
						delete(h.clients, client)
						close(client.Send)
					}
					h.mutex.Unlock()
					h.mutex.RLock()
				}
			}
			h.mutex.RUnlock()
		}
	}
}

// Broadcast sends a custom event payload to all active client screens.
func (h *Hub) Broadcast(event string, payload interface{}) error {
	rawPayload, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	msg := Message{
		Event:   event,
		Payload: rawPayload,
	}

	h.broadcast <- msg
	return nil
}

// Upgrade upgrades HTTP connections to real-time WebSockets.
func (h *Hub) Upgrade(w http.ResponseWriter, r *http.Request) (*websocket.Conn, error) {
	return h.upgrader.Upgrade(w, r, nil)
}

// RegisterClient hooks up a client to the dispatcher list.
func (h *Hub) RegisterClient(conn *websocket.Conn) {
	client := &Client{
		Hub:  h,
		Conn: conn,
		Send: make(chan Message, 256),
	}
	h.register <- client

	// Start read/write pumps
	go client.writePump()
	go client.readPump()
}

func (c *Client) readPump() {
	defer func() {
		c.Hub.unregister <- c
		c.Conn.Close()
	}()

	for {
		_, _, err := c.Conn.ReadMessage()
		if err != nil {
			break
		}
		// Schedulers only send updates, ignore client inbound messages
	}
}

func (c *Client) writePump() {
	defer func() {
		c.Conn.Close()
	}()

	for {
		msg, ok := <-c.Send
		if !ok {
			c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
			return
		}

		err := c.Conn.WriteJSON(msg)
		if err != nil {
			return
		}
	}
}
