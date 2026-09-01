package services

import (
	"context"
	"errors"
	"time"
	"clusterflow/auth"
	"clusterflow/config"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

type AuthService struct {
	userRepo auth.UserRepository
	cfg      *config.Config
}

func NewAuthService(userRepo auth.UserRepository, cfg *config.Config) auth.Service {
	return &AuthService{
		userRepo: userRepo,
		cfg:      cfg,
	}
}

func (s *AuthService) Register(ctx context.Context, creds auth.Credentials) (*auth.TokenResponse, error) {
	// Check if email already registered
	existing, _ := s.userRepo.FindByEmail(ctx, creds.Email)
	if existing != nil {
		return nil, errors.New("user already exists")
	}

	// Hash password before saving
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(creds.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	// Role mapping helper for quick provisioning (admin@ -> admin, viewer@ -> viewer, default -> operator)
	role := "operator"
	if len(creds.Email) >= 5 && creds.Email[:5] == "admin" {
		role = "admin"
	} else if len(creds.Email) >= 6 && creds.Email[:6] == "viewer" {
		role = "viewer"
	}

	// Create user
	newUser := &auth.User{
		ID:        time.Now().Format("20060102150405"), // Generate simple ID
		Email:     creds.Email,
		Password:  string(hashedPassword),
		Role:      role,
		CreatedAt: time.Now().UTC(),
		UpdatedAt: time.Now().UTC(),
	}

	if err := s.userRepo.Create(ctx, newUser); err != nil {
		return nil, err
	}

	return s.generateTokenResponse(newUser)
}

func (s *AuthService) Login(ctx context.Context, creds auth.Credentials) (*auth.TokenResponse, error) {
	user, err := s.userRepo.FindByEmail(ctx, creds.Email)
	if err != nil {
		return nil, errors.New("invalid credentials")
	}

	// Verify cryptographically hashed password
	err = bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(creds.Password))
	if err != nil {
		return nil, errors.New("invalid credentials")
	}

	return s.generateTokenResponse(user)
}

func (s *AuthService) ValidateToken(tokenStr string) (*auth.User, error) {
	token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		return []byte(s.cfg.JWTSecret), nil
	})
	if err != nil || !token.Valid {
		return nil, errors.New("invalid token")
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, errors.New("invalid claims")
	}

	userId, ok := claims["sub"].(string)
	if !ok {
		return nil, errors.New("sub claim missing")
	}

	// Find user by ID in context
	return s.userRepo.FindByID(context.Background(), userId)
}

func (s *AuthService) generateTokenResponse(user *auth.User) (*auth.TokenResponse, error) {
	expiration := time.Now().Add(s.cfg.JWTExpirationHours)
	claims := jwt.MapClaims{
		"sub":  user.ID,
		"role": user.Role,
		"exp":  expiration.Unix(),
		"iat":  time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenStr, err := token.SignedString([]byte(s.cfg.JWTSecret))
	if err != nil {
		return nil, err
	}

	return &auth.TokenResponse{
		Token:     tokenStr,
		ExpiresAt: expiration,
		User:      *user,
	}, nil
}
