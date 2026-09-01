# 🌀 ClusterFlow — Distributed Compute Job Scheduler

A production-grade distributed job scheduling platform built with **Go**, **React**, **MongoDB**, and **Docker**. ClusterFlow orchestrates compute workloads across a cluster of worker nodes with real-time monitoring, priority queuing, and intelligent placement strategies.

---

## ✨ Features

- **DAG-based Job Pipelines** — Define multi-task jobs with dependency chains
- **Priority & FIFO Scheduling** — Configurable queue policies with hot-swappable strategies
- **Intelligent Worker Placement** — FirstFit and LeastLoaded placement algorithms with CPU/memory constraints
- **Real-time Dashboard** — Live WebSocket updates for job status, worker health, and cluster metrics
- **Worker Agent Simulation** — Autonomous agents that register, heartbeat, and execute tasks
- **Role-Based Access Control** — JWT authentication with Admin/Operator/Viewer roles
- **Structured JSON Logging** — Production-grade observability across all services
- **Prometheus Metrics** — Native metrics export for monitoring integrations
- **Swagger API Docs** — Interactive OpenAPI documentation
- **Docker Compose Orchestration** — One-command deployment with scalable workers
- **CI/CD Pipeline** — GitHub Actions for linting, testing, building, and Docker validation

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│  API Server  │────▶│   MongoDB    │
│  React + TS  │ WS  │  Go + Gin    │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │  Scheduler   │
                     │   Engine     │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Worker 1 │  │ Worker 2 │  │ Worker N │
        └──────────┘  └──────────┘  └──────────┘
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API Server | http://localhost:8080 |
| API Docs | http://localhost:8080/api/v1/docs |

Scale workers:
```bash
docker compose up --build --scale agent=5
```

### Local Development

```bash
# Terminal 1 — Database
docker run -d -p 27017:27017 --name cf_mongo mongo:7

# Terminal 2 — API Server
cd backend && go mod tidy
export MONGODB_URI=mongodb://localhost:27017/clusterflow
go run cmd/server/main.go

# Terminal 3 — Worker Agent
cd backend && go run cmd/agent/main.go

# Terminal 4 — Frontend
cd frontend && npm install && npm run dev
```

---

## 📁 Project Structure

```
ClusterFlow/
├── backend/
│   ├── auth/           # User models & repository interfaces
│   ├── cmd/
│   │   ├── server/     # API server entry point
│   │   ├── agent/      # Worker agent executable
│   │   ├── simulator/  # Workload generator
│   │   ├── benchmark/  # Performance benchmarking tool
│   │   └── loadtest/   # HTTP load testing tool
│   ├── config/         # Environment configuration
│   ├── handlers/       # HTTP route controllers
│   ├── jobs/           # Job & Task domain models
│   ├── middleware/     # JWT auth & request logging
│   ├── repositories/   # MongoDB data access layer
│   ├── scheduler/      # Queue policies & placement engine
│   ├── services/       # Business logic layer
│   ├── telemetry/      # Prometheus metrics & structured logging
│   ├── websocket/      # Real-time WebSocket hub
│   └── workers/        # Worker node domain models
├── frontend/
│   └── src/
│       ├── components/ # Reusable UI components
│       ├── context/    # React contexts (WebSocket, Theme)
│       ├── features/   # Feature modules (auth, jobs, workers...)
│       └── services/   # API client layer
├── mongodb/            # MongoDB Dockerfile
├── .github/workflows/  # CI/CD pipeline
└── docker-compose.yml  # Container orchestration
```

---

## 🧪 Testing

```bash
cd backend
go test ./... -v -cover
```

---

## 📊 Benchmarking

```bash
# In-memory scheduler benchmark (100–5000 jobs)
cd backend && go run cmd/benchmark/main.go

# HTTP API load test (requires running server)
cd backend && go run cmd/loadtest/main.go
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/jobs` | Submit job |
| GET | `/api/v1/jobs` | List jobs |
| GET | `/api/v1/jobs/:id` | Job details |
| POST | `/api/v1/jobs/:id/cancel` | Cancel job |
| POST | `/api/v1/jobs/:id/retry` | Retry job |
| GET | `/api/v1/workers` | List workers |
| POST | `/api/v1/workers/register` | Register worker |
| GET | `/api/v1/scheduler/queue` | Queue status |
| GET | `/api/v1/telemetry/metrics` | Cluster metrics |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/docs` | Swagger UI |

---

## 🛠️ Tech Stack

**Backend**: Go, Gin, MongoDB Driver, JWT, Prometheus, WebSocket  
**Frontend**: React 18, TypeScript, TailwindCSS v4, React Query, Zustand  
**Infrastructure**: Docker, Docker Compose, Nginx, GitHub Actions

---

## 📄 License

MIT
