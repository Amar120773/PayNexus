package telemetry

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Metrics holds handles to Prometheus metrics definitions.
type Metrics struct {
	JobsSubmitted    prometheus.Counter
	JobsCompleted    prometheus.Counter
	JobsFailed       prometheus.Counter
	ActiveWorkers    prometheus.Gauge
	TasksRunning     prometheus.Gauge
	SchedulerLatency prometheus.Histogram
}

var globalMetrics *Metrics

// InitMetrics instantiates and registers telemetry counters and gauges.
func InitMetrics() *Metrics {
	globalMetrics = &Metrics{
		JobsSubmitted: promauto.NewCounter(prometheus.CounterOpts{
			Name: "clusterflow_jobs_submitted_total",
			Help: "The total number of jobs submitted to the scheduler",
		}),
		JobsCompleted: promauto.NewCounter(prometheus.CounterOpts{
			Name: "clusterflow_jobs_completed_total",
			Help: "The total number of jobs successfully processed",
		}),
		JobsFailed: promauto.NewCounter(prometheus.CounterOpts{
			Name: "clusterflow_jobs_failed_total",
			Help: "The total number of jobs that failed execution",
		}),
		ActiveWorkers: promauto.NewGauge(prometheus.GaugeOpts{
			Name: "clusterflow_active_workers_count",
			Help: "The current count of registered active compute workers",
		}),
		TasksRunning: promauto.NewGauge(prometheus.GaugeOpts{
			Name: "clusterflow_tasks_running_count",
			Help: "The current count of running compute tasks across the cluster",
		}),
		SchedulerLatency: promauto.NewHistogram(prometheus.HistogramOpts{
			Name:    "clusterflow_scheduler_evaluation_duration_seconds",
			Help:    "Histogram of durations spent evaluating scheduling queues",
			Buckets: prometheus.DefBuckets,
		}),
	}
	return globalMetrics
}

// GetMetrics returns the global metrics context.
func GetMetrics() *Metrics {
	if globalMetrics == nil {
		return InitMetrics()
	}
	return globalMetrics
}
