package middleware

import (
	"net/http"
	"strings"
	"clusterflow/auth"

	"github.com/gin-gonic/gin"
)

// JWTAuth matches HTTP headers Authorization: Bearer <token> and validates claims.
func JWTAuth(authService auth.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			c.Abort()
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if !(len(parts) == 2 && parts[0] == "Bearer") {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header must be Bearer token"})
			c.Abort()
			return
		}

		tokenStr := parts[1]
		user, err := authService.ValidateToken(tokenStr)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}

		// Save verified User to Gin Context for route controllers to use
		c.Set("currentUser", user)
		c.Next()
	}
}

// RequireRole guards access to specific admin-only actions.
func RequireRole(allowedRoles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userVal, exists := c.Get("currentUser")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			c.Abort()
			return
		}

		user, ok := userVal.(*auth.User)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to resolve identity context"})
			c.Abort()
			return
		}

		roleAllowed := false
		for _, role := range allowedRoles {
			if user.Role == role {
				roleAllowed = true
				break
			}
		}

		if !roleAllowed {
			c.JSON(http.StatusForbidden, gin.H{"error": "Insufficient permissions to execute this request"})
			c.Abort()
			return
		}

		c.Next()
	}
}
