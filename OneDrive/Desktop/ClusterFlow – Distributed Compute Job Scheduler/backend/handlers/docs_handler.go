package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type DocsHandler struct{}

// NewDocsHandler returns a new DocsHandler instance.
func NewDocsHandler() *DocsHandler {
	return &DocsHandler{}
}

// RenderUI serves the Swagger HTML rendering page.
func (h *DocsHandler) RenderUI(c *gin.Context) {
	c.Header("Content-Type", "text/html; charset=utf-8")
	c.String(http.StatusOK, swaggerUIHTML)
}

// GetSwaggerJSON returns the static OpenAPI 3.0 JSON specification document.
func (h *DocsHandler) GetSwaggerJSON(c *gin.Context) {
	c.Header("Content-Type", "application/json; charset=utf-8")
	c.String(http.StatusOK, swaggerJSONSpec)
}

const swaggerUIHTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>ClusterFlow API Documentation</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #0f172a; color: #f8fafc; font-family: sans-serif; }
    /* Dark mode styling overrides for premium feel */
    .swagger-ui { filter: invert(0.9) hue-rotate(180deg); }
    .swagger-ui .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" charset="UTF-8"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/api/v1/docs/swagger.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>`

const swaggerJSONSpec = `{
  "openapi": "3.0.0",
  "info": {
    "title": "ClusterFlow API",
    "version": "1.0.0",
    "description": "Production-ready REST Gateway endpoints for the ClusterFlow Distributed Compute Job Scheduler."
  },
  "servers": [
    {
      "url": "/api/v1"
    }
  ],
  "components": {
    "securitySchemes": {
      "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    }
  },
  "paths": {
    "/auth/register": {
      "post": {
        "summary": "Register a new user",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                  "email": { "type": "string" },
                  "password": { "type": "string" }
                }
              }
            }
          }
        },
        "responses": {
          "201": { "description": "User created successfully" }
        }
      }
    },
    "/auth/login": {
      "post": {
        "summary": "Authenticate user credentials",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                  "email": { "type": "string" },
                  "password": { "type": "string" }
                }
              }
            }
          }
        },
        "responses": {
          "200": { "description": "Token granted" }
        }
      }
    },
    "/jobs": {
      "post": {
        "summary": "Submit a compute job DAG",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "201": { "description": "Job enqueued" }
        }
      },
      "get": {
        "summary": "List all jobs",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/jobs/{id}": {
      "get": {
        "summary": "Fetch job details by ID",
        "security": [{ "BearerAuth": [] }],
        "parameters": [
          { "name": "id", "in": "path", "required": true, "schema": { "type": "string" } }
        ],
        "responses": {
          "200": { "description": "Success" }
        }
      },
      "delete": {
        "summary": "Cancel job execution",
        "security": [{ "BearerAuth": [] }],
        "parameters": [
          { "name": "id", "in": "path", "required": true, "schema": { "type": "string" } }
        ],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/jobs/{id}/retry": {
      "post": {
        "summary": "Retry a failed/cancelled job",
        "security": [{ "BearerAuth": [] }],
        "parameters": [
          { "name": "id", "in": "path", "required": true, "schema": { "type": "string" } }
        ],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/workers": {
      "get": {
        "summary": "List active worker compute nodes",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/workers/{id}": {
      "get": {
        "summary": "Get worker node specifications",
        "security": [{ "BearerAuth": [] }],
        "parameters": [
          { "name": "id", "in": "path", "required": true, "schema": { "type": "string" } }
        ],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/scheduler/queue": {
      "get": {
        "summary": "Fetch active scheduler wait queue details",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/scheduler/policy": {
      "post": {
        "summary": "Override active scheduling strategies",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/telemetry/metrics": {
      "get": {
        "summary": "Fetch timeseries historical snapshots",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/telemetry/status": {
      "get": {
        "summary": "Fetch aggregated cluster status summaries",
        "security": [{ "BearerAuth": [] }],
        "responses": {
          "200": { "description": "Success" }
        }
      }
    },
    "/health": {
      "get": {
        "summary": "Verify gateway health diagnostics",
        "responses": {
          "200": { "description": "Success" }
        }
      }
    }
  }
}`
