package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds all configuration variables for the application.
type Config struct {
	ServerPort         string
	MongoURI           string
	DBName             string
	JWTSecret          string
	JWTExpirationHours time.Duration
	Environment        string // "development", "production", "testing"
	MetricsPort        string
	WSReadBufferSize   int
	WSWriteBufferSize  int
}

// LoadConfig loads variables from environment and applies default values if empty.
func LoadConfig() *Config {
	env := getEnv("ENV", "development")

	jwtExpHours, err := strconv.Atoi(getEnv("JWT_EXPIRATION_HOURS", "24"))
	if err != nil {
		jwtExpHours = 24
	}

	wsReadBuf, err := strconv.Atoi(getEnv("WS_READ_BUFFER_SIZE", "1024"))
	if err != nil {
		wsReadBuf = 1024
	}

	wsWriteBuf, err := strconv.Atoi(getEnv("WS_WRITE_BUFFER_SIZE", "1024"))
	if err != nil {
		wsWriteBuf = 1024
	}

	return &Config{
		ServerPort:         getEnv("PORT", "8080"),
		MongoURI:           getEnv("MONGODB_URI", "mongodb://localhost:27017"),
		DBName:             getEnv("DB_NAME", "clusterflow"),
		JWTSecret:          getEnv("JWT_SECRET", "super_secret_clusterflow_key_change_me_in_prod"),
		JWTExpirationHours: time.Duration(jwtExpHours) * time.Hour,
		Environment:        env,
		MetricsPort:        getEnv("METRICS_PORT", "9090"),
		WSReadBufferSize:   wsReadBuf,
		WSWriteBufferSize:  wsWriteBuf,
	}
}

// Helper function to read environment variables with a fallback default.
func getEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}
