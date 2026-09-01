package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

type Config struct {
	ServerURL     string
	AdminEmail    string
	AdminPassword string
}

type TaskPayload struct {
	ID                 string   `json:"id"`
	Name               string   `json:"name"`
	Command            string   `json:"command"`
	RequiredCores      int      `json:"requiredCores"`
	RequiredMemory     int64    `json:"requiredMemoryBytes"`
	MaxRetries         int      `json:"maxRetries"`
	DurationSeconds    int      `json:"durationSeconds"`
	FailureProbability float64  `json:"failureProbability"`
	DependsOn          []string `json:"dependsOn"`
}

type JobPayload struct {
	Name        string        `json:"name"`
	Description string        `json:"description"`
	Priority    int           `json:"priority"`
	Tasks       []TaskPayload `json:"tasks"`
}

type TokenResponse struct {
	Token string `json:"token"`
}

type Simulator struct {
	cfg        Config
	jwtToken   string
	httpClient *http.Client
}

func main() {
	cfg := Config{
		ServerURL:     getEnv("SERVER_URL", "http://localhost:8080/api/v1"),
		AdminEmail:    getEnv("ADMIN_EMAIL", "admin@clusterflow.io"),
		AdminPassword: getEnv("ADMIN_PASSWORD", "adminpassword"),
	}

	fmt.Println("[SIMULATOR] Starting Workload Generator...")

	sim := &Simulator{
		cfg:        cfg,
		httpClient: &http.Client{Timeout: 5 * time.Second},
	}

	// Bootstrap Auth
	sim.bootstrapAuth()

	// Control context
	ctx, cancel := contextWithSignals()
	defer cancel()

	fmt.Println("[SIMULATOR] Workload runner activated. Submitting random jobs every 4 seconds. Press Ctrl+C to stop.")
	ticker := time.NewTicker(4 * time.Second)
	defer ticker.Stop()

	jobCounter := 1

	for {
		select {
		case <-ctx.Done():
			fmt.Println("[SIMULATOR] Shutting down Workload Generator...")
			return
		case <-ticker.C:
			sim.submitRandomJob(jobCounter)
			jobCounter++
		}
	}
}

func (s *Simulator) bootstrapAuth() {
	token, err := s.login()
	if err != nil {
		fmt.Println("[SIMULATOR] Admin login failed, bootstrapping account...")
		if regErr := s.register(); regErr != nil {
			fmt.Printf("[SIMULATOR] Registration fallback failed: %v. Retrying in 5s...\n", regErr)
			time.Sleep(5 * time.Second)
			s.bootstrapAuth()
			return
		}
		token, err = s.login()
		if err != nil {
			fmt.Printf("[SIMULATOR] Login post-registration failed: %v. Retrying in 5s...\n", err)
			time.Sleep(5 * time.Second)
			s.bootstrapAuth()
			return
		}
	}
	s.jwtToken = token
	fmt.Println("[SIMULATOR] Connected to server successfully.")
}

func (s *Simulator) login() (string, error) {
	payload := map[string]string{
		"email":    s.cfg.AdminEmail,
		"password": s.cfg.AdminPassword,
	}
	jsonBytes, _ := json.Marshal(payload)

	resp, err := s.httpClient.Post(fmt.Sprintf("%s/auth/login", s.cfg.ServerURL), "application/json", bytes.NewBuffer(jsonBytes))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("status %d", resp.StatusCode)
	}

	var res TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return "", err
	}
	return res.Token, nil
}

func (s *Simulator) register() error {
	payload := map[string]string{
		"email":    s.cfg.AdminEmail,
		"password": s.cfg.AdminPassword,
	}
	jsonBytes, _ := json.Marshal(payload)

	resp, err := s.httpClient.Post(fmt.Sprintf("%s/auth/register", s.cfg.ServerURL), "application/json", bytes.NewBuffer(jsonBytes))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("status %d: %s", resp.StatusCode, string(body))
	}
	return nil
}

func (s *Simulator) submitRandomJob(index int) {
	priorities := []int{1, 2, 3, 5, 8, 10}
	priority := priorities[rand.Intn(len(priorities))]

	coresOpts := []int{1, 2, 4}
	memOpts := []int64{512 * 1024 * 1024, 1024 * 1024 * 1024, 2048 * 1024 * 1024}

	// Random DAG structures
	jobType := rand.Intn(3)
	var tasks []TaskPayload

	switch jobType {
	case 0:
		// Single independent task
		tasks = []TaskPayload{
			{
				ID:                 "task-01",
				Name:               "AnalyzeData",
				Command:            "analyze",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         2,
				DurationSeconds:    3 + rand.Intn(6),
				FailureProbability: rand.Float64() * 0.20, // 0 to 20%
				DependsOn:          []string{},
			},
		}
	case 1:
		// Linear pipeline: task-01 -> task-02
		tasks = []TaskPayload{
			{
				ID:                 "task-01",
				Name:               "FetchLogs",
				Command:            "fetch",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         3,
				DurationSeconds:    3 + rand.Intn(4),
				FailureProbability: rand.Float64() * 0.10,
				DependsOn:          []string{},
			},
			{
				ID:                 "task-02",
				Name:               "ProcessLogs",
				Command:            "process",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         2,
				DurationSeconds:    4 + rand.Intn(6),
				FailureProbability: rand.Float64() * 0.15,
				DependsOn:          []string{"task-01"},
			},
		}
	case 2:
		// Fork/Join graph: task-01 -> task-02A + task-02B -> task-03
		tasks = []TaskPayload{
			{
				ID:                 "task-01",
				Name:               "IngestStream",
				Command:            "ingest",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         3,
				DurationSeconds:    4 + rand.Intn(4),
				FailureProbability: 0.05,
				DependsOn:          []string{},
			},
			{
				ID:                 "task-02A",
				Name:               "ExtractFeatures",
				Command:            "extract",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         2,
				DurationSeconds:    3 + rand.Intn(5),
				FailureProbability: rand.Float64() * 0.25,
				DependsOn:          []string{"task-01"},
			},
			{
				ID:                 "task-02B",
				Name:               "GenerateEmbeddings",
				Command:            "embed",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         2,
				DurationSeconds:    3 + rand.Intn(5),
				FailureProbability: rand.Float64() * 0.10,
				DependsOn:          []string{"task-01"},
			},
			{
				ID:                 "task-03",
				Name:               "SaveToDB",
				Command:            "save",
				RequiredCores:      coresOpts[rand.Intn(len(coresOpts))],
				RequiredMemory:     memOpts[rand.Intn(len(memOpts))],
				MaxRetries:         3,
				DurationSeconds:    2 + rand.Intn(3),
				FailureProbability: 0.02,
				DependsOn:          []string{"task-02A", "task-02B"},
			},
		}
	}

	job := JobPayload{
		Name:        fmt.Sprintf("Simulated-Job-%03d", index),
		Description: fmt.Sprintf("Cluster stress test job generation sequence #%d", index),
		Priority:    priority,
		Tasks:       tasks,
	}

	jsonBytes, _ := json.Marshal(job)
	req, _ := http.NewRequest("POST", fmt.Sprintf("%s/jobs", s.cfg.ServerURL), bytes.NewBuffer(jsonBytes))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", s.jwtToken))

	resp, err := s.httpClient.Do(req)
	if err != nil {
		fmt.Printf("[SIMULATOR] Failed to submit Job [%s]: %v\n", job.Name, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("[SIMULATOR] Server rejected Job [%s]: Status %d - %s\n", job.Name, resp.StatusCode, string(body))
		return
	}

	fmt.Printf("[SIMULATOR] Submitted job '%s' containing %d tasks (Priority: %d)\n", job.Name, len(job.Tasks), job.Priority)
}

func getEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}

func contextWithSignals() (context.Context, context.CancelFunc) {
	ctx, cancel := context.WithCancel(context.Background())
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		cancel()
	}()
	return ctx, cancel
}
