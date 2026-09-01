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
	"sync"
	"syscall"
	"time"
)

// Configurations mapping environment settings
type AgentConfig struct {
	AgentID       string
	ServerURL     string
	Cores         int
	MemoryGB      int64
	AdminEmail    string
	AdminPassword string
}

type ResourceStats struct {
	CPUCores         int     `json:"cpuCores"`
	CPUUsagePercent  float64 `json:"cpuUsagePercent"`
	TotalMemoryBytes int64   `json:"totalMemoryBytes"`
	UsedMemoryBytes  int64   `json:"usedMemoryBytes"`
	TotalDiskBytes   int64   `json:"totalDiskBytes"`
	UsedDiskBytes    int64   `json:"usedDiskBytes"`
}

type WorkerNode struct {
	ID        string        `json:"id"`
	Hostname  string        `json:"hostname"`
	IPAddress string        `json:"ipAddress"`
	State     string        `json:"state"`
	Resources ResourceStats `json:"resources"`
}

type HeartbeatPayload struct {
	WorkerID     string        `json:"workerId"`
	Resources    ResourceStats `json:"resources"`
	RunningTasks []string      `json:"runningTasks"`
}

type TaskResultPayload struct {
	ExitCode int      `json:"exitCode"`
	ErrorLog string   `json:"errorLog,omitempty"`
	Logs     []string `json:"logs"`
}

type Task struct {
	ID                 string    `json:"id"`
	Name               string    `json:"name"`
	Command            string    `json:"command"`
	State              string    `json:"state"`
	RequiredCores      int       `json:"requiredCores"`
	RequiredMemory     int64     `json:"requiredMemoryBytes"`
	DurationSeconds    int       `json:"durationSeconds"`
	FailureProbability float64   `json:"failureProbability"`
	AssignedNode       string    `json:"assignedNode"`
	ExitCode           int       `json:"exitCode"`
	StartedAt          time.Time `json:"startedAt"`
	FinishedAt         time.Time `json:"finishedAt"`
}

type Job struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	State     string `json:"state"`
	Tasks     []Task `json:"tasks"`
	Variables map[string]string `json:"variables"`
}

type TokenResponse struct {
	Token string `json:"token"`
}

type Agent struct {
	cfg          AgentConfig
	jwtToken     string
	runningTasks map[string]Task // key: taskId
	mutex        sync.Mutex
	httpClient   *http.Client
}

func main() {
	// 1. Load Configurations
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "node-01"
	}
	cfg := AgentConfig{
		AgentID:       getEnv("AGENT_ID", "agent-"+hostname),
		ServerURL:     getEnv("SERVER_URL", "http://localhost:8080/api/v1"),
		Cores:         4,
		MemoryGB:      16,
		AdminEmail:    getEnv("ADMIN_EMAIL", "admin@clusterflow.io"),
		AdminPassword: getEnv("ADMIN_PASSWORD", "adminpassword"),
	}

	fmt.Printf("[AGENT] Starting ClusterFlow Agent [%s]...\n", cfg.AgentID)

	agent := &Agent{
		cfg:          cfg,
		runningTasks: make(map[string]Task),
		httpClient:   &http.Client{Timeout: 5 * time.Second},
	}

	// 2. Perform Authentication and Registration bootstrap
	agent.bootstrapAuthAndRegistration()

	// 3. Start Loops
	ctx, cancel := contextWithSignals()
	defer cancel()

	var wg sync.WaitGroup
	wg.Add(2)

	// Heartbeat Loop
	go func() {
		defer wg.Done()
		ticker := time.NewTicker(3 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				agent.sendHeartbeat()
			}
		}
	}()

	// Polling Loop
	go func() {
		defer wg.Done()
		ticker := time.NewTicker(1 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				agent.pollForTasks()
			}
		}
	}()

	<-ctx.Done()
	fmt.Println("[AGENT] Gracefully shutting down worker agent...")
	wg.Wait()
	fmt.Println("[AGENT] Worker agent terminated successfully.")
}

func (a *Agent) bootstrapAuthAndRegistration() {
	// Try login
	token, err := a.login()
	if err != nil {
		fmt.Println("[AGENT] Admin account not found or invalid, attempting registration...")
		// Auto register admin account in dry setup
		if errReg := a.register(); errReg != nil {
			fmt.Printf("[AGENT] Registration failed: %v. Retrying connection in 5s...\n", errReg)
			time.Sleep(5 * time.Second)
			a.bootstrapAuthAndRegistration()
			return
		}
		// Attempt login again after registration
		token, err = a.login()
		if err != nil {
			fmt.Printf("[AGENT] Login failed post-registration: %v. Retrying in 5s...\n", err)
			time.Sleep(5 * time.Second)
			a.bootstrapAuthAndRegistration()
			return
		}
	}
	a.jwtToken = token
	fmt.Println("[AGENT] Authenticated successfully.")

	// Register Worker specs
	err = a.registerWorkerNode()
	if err != nil {
		fmt.Printf("[AGENT] Node registration failed: %v. Retrying in 5s...\n", err)
		time.Sleep(5 * time.Second)
		a.bootstrapAuthAndRegistration()
		return
	}
	fmt.Println("[AGENT] Compute node registered to master cluster.")
}

func (a *Agent) login() (string, error) {
	payload := map[string]string{
		"email":    a.cfg.AdminEmail,
		"password": a.cfg.AdminPassword,
	}
	jsonBytes, _ := json.Marshal(payload)

	resp, err := a.httpClient.Post(fmt.Sprintf("%s/auth/login", a.cfg.ServerURL), "application/json", bytes.NewBuffer(jsonBytes))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("http error %d", resp.StatusCode)
	}

	var data TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return "", err
	}
	return data.Token, nil
}

func (a *Agent) register() error {
	payload := map[string]string{
		"email":    a.cfg.AdminEmail,
		"password": a.cfg.AdminPassword,
	}
	jsonBytes, _ := json.Marshal(payload)

	resp, err := a.httpClient.Post(fmt.Sprintf("%s/auth/register", a.cfg.ServerURL), "application/json", bytes.NewBuffer(jsonBytes))
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

func (a *Agent) registerWorkerNode() error {
	hostname, _ := os.Hostname()
	node := WorkerNode{
		ID:        a.cfg.AgentID,
		Hostname:  hostname,
		IPAddress: "127.0.0.1",
		State:     "ACTIVE",
		Resources: ResourceStats{
			CPUCores:         a.cfg.Cores,
			CPUUsagePercent:  0.0,
			TotalMemoryBytes: a.cfg.MemoryGB * 1024 * 1024 * 1024,
			UsedMemoryBytes:  0,
			TotalDiskBytes:   100 * 1024 * 1024 * 1024,
			UsedDiskBytes:    0,
		},
	}
	jsonBytes, _ := json.Marshal(node)

	req, _ := http.NewRequest("POST", fmt.Sprintf("%s/workers", a.cfg.ServerURL), bytes.NewBuffer(jsonBytes))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", a.jwtToken))

	resp, err := a.httpClient.Do(req)
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

func (a *Agent) sendHeartbeat() {
	a.mutex.Lock()
	runningCount := len(a.runningTasks)
	runningIDs := make([]string, 0, runningCount)
	var allocatedMem int64
	var allocatedCores int
	for id, t := range a.runningTasks {
		runningIDs = append(runningIDs, id)
		allocatedMem += t.RequiredMemory
		allocatedCores += t.RequiredCores
	}
	a.mutex.Unlock()

	// Calculate CPU usage from allocated task cores + a dynamic drift (-10% to +10%)
	coresRatio := float64(allocatedCores) / float64(a.cfg.Cores)
	if coresRatio > 1.0 {
		coresRatio = 1.0
	}
	cpuUsage := (coresRatio * 100.0) + (rand.Float64()*20.0 - 10.0)
	if cpuUsage < 2.0 {
		cpuUsage = 2.0 // baseline OS idle load
	} else if cpuUsage > 100.0 {
		cpuUsage = 100.0
	}

	// Memory usage fluctuates slightly (-50MB to +50MB) to simulate runtime dynamic consumption
	drift := int64((rand.Float64()*100.0 - 50.0) * 1024 * 1024)
	usedMem := (2 * 1024 * 1024 * 1024) + allocatedMem + drift
	if usedMem < 100*1024*1024 {
		usedMem = 100 * 1024 * 1024
	}

	payload := HeartbeatPayload{
		WorkerID: a.cfg.AgentID,
		Resources: ResourceStats{
			CPUCores:         a.cfg.Cores,
			CPUUsagePercent:  cpuUsage,
			TotalMemoryBytes: a.cfg.MemoryGB * 1024 * 1024 * 1024,
			UsedMemoryBytes:  usedMem,
			TotalDiskBytes:   100 * 1024 * 1024 * 1024,
			UsedDiskBytes:    5 * 1024 * 1024 * 1024,
		},
		RunningTasks: runningIDs,
	}

	jsonBytes, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", fmt.Sprintf("%s/workers/heartbeat", a.cfg.ServerURL), bytes.NewBuffer(jsonBytes))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", a.jwtToken))

	resp, err := a.httpClient.Do(req)
	if err != nil {
		fmt.Printf("[AGENT] Heartbeat transmission failed: %v\n", err)
		return
	}
	resp.Body.Close()
}

func (a *Agent) pollForTasks() {
	req, _ := http.NewRequest("GET", fmt.Sprintf("%s/workers/%s/tasks", a.cfg.ServerURL, a.cfg.AgentID), nil)
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", a.jwtToken))

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return
	}

	var activeJobs []Job
	if err := json.NewDecoder(resp.Body).Decode(&activeJobs); err != nil {
		return
	}

	for _, job := range activeJobs {
		for _, task := range job.Tasks {
			if task.AssignedNode == a.cfg.AgentID && task.State == "RUNNING" {
				a.mutex.Lock()
				_, alreadyRunning := a.runningTasks[task.ID]
				if !alreadyRunning {
					a.runningTasks[task.ID] = task
					go a.executeTask(job.ID, task)
				}
				a.mutex.Unlock()
			}
		}
	}
}

func (a *Agent) executeTask(jobID string, task Task) {
	fmt.Printf("[AGENT] Task [%s] matching command '%s' accepted. Executing...\n", task.ID, task.Command)

	durationSecs := task.DurationSeconds
	if durationSecs <= 0 {
		durationSecs = 3 + rand.Intn(6) // default random runtime 3 to 8s
	}

	var logs []string
	for i := 1; i <= durationSecs; i++ {
		logMsg := fmt.Sprintf("[%s] Task %s - Step %d/%d: Executing operations (Allocated CPU: %d cores, Memory: %dMB)...",
			time.Now().Format("15:04:05"), task.ID, i, durationSecs, task.RequiredCores, task.RequiredMemory/(1024*1024))
		fmt.Println("[AGENT]", logMsg)
		logs = append(logs, logMsg)
		time.Sleep(1 * time.Second)
	}

	exitCode := 0
	var errorLog string

	// Evaluate failures based on Probability
	failProb := task.FailureProbability
	if task.Command == "fail" {
		failProb = 1.0
	}

	if rand.Float64() < failProb {
		exitCode = 1
		errorLog = fmt.Sprintf("Process exited with status code 1: Task simulation failed randomly matching probability %.2f", failProb)
		logMsg := fmt.Sprintf("[%s] Task %s - ERROR: %s", time.Now().Format("15:04:05"), task.ID, errorLog)
		fmt.Println("[AGENT]", logMsg)
		logs = append(logs, logMsg)
	} else {
		logMsg := fmt.Sprintf("[%s] Task %s - Completed successfully.", time.Now().Format("15:04:05"), task.ID)
		fmt.Println("[AGENT]", logMsg)
		logs = append(logs, logMsg)
	}

	// Submit results back
	payload := TaskResultPayload{
		ExitCode: exitCode,
		ErrorLog: errorLog,
		Logs:     logs,
	}

	jsonBytes, _ := json.Marshal(payload)
	url := fmt.Sprintf("%s/workers/%s/tasks/%s/result?jobId=%s", a.cfg.ServerURL, a.cfg.AgentID, task.ID, jobID)
	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(jsonBytes))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", a.jwtToken))

	resp, err := a.httpClient.Do(req)
	
	a.mutex.Lock()
	delete(a.runningTasks, task.ID)
	a.mutex.Unlock()

	if err != nil {
		fmt.Printf("[AGENT] Failed to report status for Task [%s]: %v\n", task.ID, err)
		return
	}
	resp.Body.Close()

	if exitCode == 0 {
		fmt.Printf("[AGENT] Task [%s] reported success.\n", task.ID)
	} else {
		fmt.Printf("[AGENT] Task [%s] reported simulation failure.\n", task.ID)
	}
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
