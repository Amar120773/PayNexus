package telemetry

import (
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// LogLevel defines the severity level of log logs.
type LogLevel string

const (
	LevelDebug LogLevel = "DEBUG"
	LevelInfo  LogLevel = "INFO"
	LevelWarn  LogLevel = "WARN"
	LevelError LogLevel = "ERROR"
)

// LogFields is a map of contextual keys/values logged alongside messages.
type LogFields map[string]interface{}

// Logger defines structured logging actions.
type Logger interface {
	Debug(msg string, fields LogFields)
	Info(msg string, fields LogFields)
	Warn(msg string, fields LogFields)
	Error(msg string, fields LogFields)
}

// GlobalLogger is a globally accessible Logger instance initialized at startup.
var GlobalLogger Logger = &JSONLogger{env: "development"}

// JSONLogger is a production-ready structured console logger.
type JSONLogger struct {
	env string
}

// NewLogger creates a new structured JSON logger.
func NewLogger(env string) Logger {
	return &JSONLogger{env: env}
}

func (l *JSONLogger) log(level LogLevel, msg string, fields LogFields) {
	if fields == nil {
		fields = make(LogFields)
	}
	fields["level"] = level
	fields["message"] = msg
	fields["timestamp"] = time.Now().UTC().Format(time.RFC3339Nano)
	fields["env"] = l.env

	bytes, err := json.Marshal(fields)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to marshal log fields: %v\n", err)
		return
	}

	if level == LevelError {
		fmt.Fprintln(os.Stderr, string(bytes))
	} else {
		fmt.Fprintln(os.Stdout, string(bytes))
	}
}

func (l *JSONLogger) Debug(msg string, fields LogFields) {
	l.log(LevelDebug, msg, fields)
}

func (l *JSONLogger) Info(msg string, fields LogFields) {
	l.log(LevelInfo, msg, fields)
}

func (l *JSONLogger) Warn(msg string, fields LogFields) {
	l.log(LevelWarn, msg, fields)
}

func (l *JSONLogger) Error(msg string, fields LogFields) {
	l.log(LevelError, msg, fields)
}
