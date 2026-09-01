package auth

import (
	"context"
	"time"
)

// User represents the system operator or client in ClusterFlow.
type User struct {
	ID        string    `json:"id" bson:"_id,omitempty"`
	Email     string    `json:"email" bson:"email"`
	Password  string    `json:"-" bson:"password"` // Hashed, never exposed in JSON
	Role      string    `json:"role" bson:"role"`   // "admin", "operator", "viewer"
	CreatedAt time.Time `json:"createdAt" bson:"createdAt"`
	UpdatedAt time.Time `json:"updatedAt" bson:"updatedAt"`
}

// Credentials is used during authentication requests.
type Credentials struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=6"`
}

// TokenResponse represents the JWT payload returned on successful login.
type TokenResponse struct {
	Token     string    `json:"token"`
	ExpiresAt time.Time `json:"expiresAt"`
	User      User      `json:"user"`
}

// UserRepository defines the interfaces for persisting user data.
type UserRepository interface {
	Create(ctx context.Context, user *User) error
	FindByEmail(ctx context.Context, email string) (*User, error)
	FindByID(ctx context.Context, id string) (*User, error)
}

// Service defines the core authentication and authorization actions.
type Service interface {
	Register(ctx context.Context, creds Credentials) (*TokenResponse, error)
	Login(ctx context.Context, creds Credentials) (*TokenResponse, error)
	ValidateToken(tokenStr string) (*User, error)
}
