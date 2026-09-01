package logger

import (
	"log/slog"
	"os"
	"sync"
)

var (
	once sync.Once
)

// InitLogger sets up a global structured JSON logger writing to os.Stdout.
func InitLogger() {
	once.Do(func() {
		handler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
			Level: slog.LevelInfo,
		})
		logger := slog.New(handler)
		slog.SetDefault(logger)
	})
}

// Info logs messages with structured context attributes.
func Info(msg string, args ...interface{}) {
	slog.Info(msg, args...)
}

// Error logs errors with structured context attributes.
func Error(msg string, args ...interface{}) {
	slog.Error(msg, args...)
}

// Warn logs warnings with structured context attributes.
func Warn(msg string, args ...interface{}) {
	slog.Warn(msg, args...)
}

// Debug logs debug records with structured context attributes.
func Debug(msg string, args ...interface{}) {
	slog.Debug(msg, args...)
}
