package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"clusterflow/config"
	"clusterflow/handlers"
	"clusterflow/jobs"
	"clusterflow/middleware"
	"clusterflow/repositories"
	"clusterflow/scheduler"
	"clusterflow/services"
	"clusterflow/telemetry"
	"clusterflow/websocket"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func main() {
	// 1. Load Configurations
	cfg := config.LoadConfig()

	// 2. Initialize Telemetry Logger
	telemetry.GlobalLogger = telemetry.NewLogger(cfg.Environment)
	log := telemetry.GlobalLogger
	log.Info("Starting ClusterFlow Distributed Scheduler Service...", telemetry.LogFields{
		"env":         cfg.Environment,
		"port":        cfg.ServerPort,
		"metricsPort": cfg.MetricsPort,
	})

	// 3. Initialize Prometheus Metrics
	_ = telemetry.InitMetrics()

	// 4. Initialize MongoDB Connection
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	mongoClient, err := mongo.Connect(ctx, options.Client().ApplyURI(cfg.MongoURI))
	var db *mongo.Database
	if err != nil {
		log.Error("Failed to configure MongoDB client, running in fallback dry mode", telemetry.LogFields{"error": err.Error()})
	} else {
		// Ping database to verify connection
		err = mongoClient.Ping(ctx, nil)
		if err != nil {
			log.Warn("MongoDB service not reachable, queries will block or fail. Verify server connection.", telemetry.LogFields{"uri": cfg.MongoURI})
		}
		db = mongoClient.Database(cfg.DBName)

		// Setup database indexes
		if errIndex := repositories.InitializeIndexes(ctx, db); errIndex != nil {
			log.Error("Failed to construct database collection indexes", telemetry.LogFields{"error": errIndex.Error()})
		} else {
			log.Info("Database performance and unique constraint indexes configured successfully", nil)
		}
	}

	// 5. Initialize Repositories (Fallback to mock values if MongoDB Database connection is nil)
	var userRepo repositories.MongoUserRepository
	var jobRepo repositories.MongoJobRepository
	var workerRepo repositories.MongoWorkerRepository
	var queueRepo scheduler.QueueRepository
	var historyRepo jobs.HistoryRepository
	var metricsRepo telemetry.MetricsRepository

	if db != nil {
		userRepo = *repositories.NewMongoUserRepository(db).(*repositories.MongoUserRepository)
		jobRepo = *repositories.NewMongoJobRepository(db).(*repositories.MongoJobRepository)
		workerRepo = *repositories.NewMongoWorkerRepository(db).(*repositories.MongoWorkerRepository)
		queueRepo = repositories.NewMongoQueueRepository(db)
		historyRepo = repositories.NewMongoHistoryRepository(db)
		metricsRepo = repositories.NewMongoMetricsRepository(db)
	}

	// 6. Initialize WebSocket Hub
	wsHub := websocket.NewHub(cfg.WSReadBufferSize, cfg.WSWriteBufferSize)
	go wsHub.Run()
	log.Info("Real-time WebSocket event broadcaster hub started", nil)

	// 7. Initialize Scheduler Engine
	sched := scheduler.NewSchedulerEngine(&jobRepo, &workerRepo, queueRepo, historyRepo, wsHub)
	err = sched.Start(context.Background())
	if err != nil {
		log.Error("Failed to initiate Scheduler core execution loop", telemetry.LogFields{"error": err.Error()})
		return
	}
	defer sched.Stop()
	log.Info("Scheduler evaluation loops running", nil)

	// 8. Initialize Service Layer
	authService := services.NewAuthService(&userRepo, cfg)
	jobService := services.NewJobService(&jobRepo, sched, wsHub)
	workerService := services.NewWorkerService(&workerRepo, &jobRepo, historyRepo, sched, wsHub)

	if db != nil {
		telemetryService := services.NewTelemetryService(metricsRepo, &jobRepo, &workerRepo, queueRepo, historyRepo, wsHub)
		telemetryService.Start(context.Background())
		log.Info("Telemetry aggregation daemon started", nil)
	}

	// 9. Initialize HTTP Handlers
	authHandler := handlers.NewAuthHandler(authService)
	jobHandler := handlers.NewJobHandler(jobService)
	workerHandler := handlers.NewWorkerHandler(workerService)
	wsHandler := handlers.NewWebSocketHandler(wsHub)
	healthHandler := handlers.NewHealthHandler(mongoClient)
	schedulerHandler := handlers.NewSchedulerHandler(sched, queueRepo)
	telemetryHandler := handlers.NewTelemetryHandler(metricsRepo, &jobRepo, &workerRepo)
	docsHandler := handlers.NewDocsHandler()

	// 10. Setup Gin Router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	r := gin.New()

	// Default Middlewares
	r.Use(middleware.RequestID())
	r.Use(gin.Recovery())
	r.Use(middleware.RequestTelemetry(log))

	// CORS Middleware Skeleton
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	})

	// 11. Register Endpoints
	api := r.Group("/api/v1")
	{
		// Health Endpoint (Public)
		api.GET("/health", healthHandler.HealthCheck)

		// Swagger Documentation Routes (Public)
		api.GET("/docs", docsHandler.RenderUI)
		api.GET("/docs/swagger.json", docsHandler.GetSwaggerJSON)

		// Authentication Routes (Public)
		authGroup := api.Group("/auth")
		{
			authGroup.POST("/register", authHandler.Register)
			authGroup.POST("/login", authHandler.Login)
		}

		// Protected Route Group
		protected := api.Group("/")
		protected.Use(middleware.JWTAuth(authService))
		{
			// Jobs endpoints
			jobsGroup := protected.Group("/jobs")
			{
				jobsGroup.POST("", middleware.RequireRole("admin", "operator"), jobHandler.Submit)
				jobsGroup.GET("", jobHandler.List)
				jobsGroup.GET("/:id", jobHandler.GetByID)
				jobsGroup.POST("/:id/retry", middleware.RequireRole("admin", "operator"), jobHandler.Retry)
				jobsGroup.DELETE("/:id", middleware.RequireRole("admin", "operator"), jobHandler.Cancel)
			}

			// Workers endpoints
			workersGroup := protected.Group("/workers")
			{
				workersGroup.POST("", middleware.RequireRole("admin"), workerHandler.Register)
				workersGroup.GET("", workerHandler.List)
				workersGroup.GET("/:id", workerHandler.GetByID)
				workersGroup.POST("/heartbeat", workerHandler.Heartbeat)
				workersGroup.GET("/:id/tasks", workerHandler.GetTasks)
				workersGroup.POST("/:id/tasks/:taskId/result", workerHandler.SubmitResult)
			}

			// Scheduler endpoints
			schedulerGroup := protected.Group("/scheduler")
			{
				schedulerGroup.GET("/queue", schedulerHandler.GetQueue)
				schedulerGroup.POST("/policy", middleware.RequireRole("admin"), schedulerHandler.SetPolicy)
			}

			// Telemetry endpoints
			telemetryGroup := protected.Group("/telemetry")
			{
				telemetryGroup.GET("/metrics", telemetryHandler.GetMetrics)
				telemetryGroup.GET("/status", telemetryHandler.GetClusterStatus)
			}

			// WebSocket Real-time upgrade
			protected.GET("/ws", wsHandler.Connect)
		}
	}

	// 12. Run Prometheus Metrics endpoint on a secondary port (standard cloud deployment layout)
	go func() {
		metricsMux := http.NewServeMux()
		metricsMux.Handle("/metrics", promhttp.Handler())
		metricsServer := &http.Server{
			Addr:    fmt.Sprintf(":%s", cfg.MetricsPort),
			Handler: metricsMux,
		}
		log.Info(fmt.Sprintf("Prometheus metrics server exporting metrics on http://localhost:%s/metrics", cfg.MetricsPort), nil)
		if err := metricsServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Warn("Prometheus metrics registry stopped", telemetry.LogFields{"error": err.Error()})
		}
	}()

	// 13. Graceful Server Shutdown Setup
	server := &http.Server{
		Addr:    fmt.Sprintf(":%s", cfg.ServerPort),
		Handler: r,
	}

	go func() {
		log.Info(fmt.Sprintf("ClusterFlow Gateway API serving on http://localhost:%s", cfg.ServerPort), nil)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Error("Gateway HTTP server crashed", telemetry.LogFields{"error": err.Error()})
		}
	}()

	// Listen for interrupt signals
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("Shutting down servers...", nil)
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Error("API Server forced to shutdown", telemetry.LogFields{"error": err.Error()})
	}

	log.Info("ClusterFlow Scheduler service stopped successfully.", nil)
}
