package repositories

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// InitializeIndexes creates required indexes and unique constraints on MongoDB.
func InitializeIndexes(ctx context.Context, db *mongo.Database) error {
	// 1. User collection indexes
	usersCol := db.Collection("users")
	_, err := usersCol.Indexes().CreateOne(ctx, mongo.IndexModel{
		Keys:    bson.D{{Key: "email", Value: 1}},
		Options: options.Index().SetUnique(true),
	})
	if err != nil {
		return err
	}

	// 2. Jobs collection indexes
	jobsCol := db.Collection("jobs")
	_, err = jobsCol.Indexes().CreateMany(ctx, []mongo.IndexModel{
		{
			Keys: bson.D{{Key: "state", Value: 1}},
		},
		{
			// Compound index to speed up priority sorting evaluations
			Keys: bson.D{{Key: "priority", Value: -1}, {Key: "createdAt", Value: 1}},
		},
		{
			Keys: bson.D{{Key: "creatorId", Value: 1}},
		},
	})
	if err != nil {
		return err
	}

	// 3. Workers collection indexes
	workersCol := db.Collection("workers")
	_, err = workersCol.Indexes().CreateMany(ctx, []mongo.IndexModel{
		{
			Keys: bson.D{{Key: "state", Value: 1}},
		},
		{
			Keys: bson.D{{Key: "lastHeartbeat", Value: 1}},
		},
	})
	if err != nil {
		return err
	}

	// 4. Persistent queue collection indexes
	queueCol := db.Collection("queue")
	_, err = queueCol.Indexes().CreateMany(ctx, []mongo.IndexModel{
		{
			Keys:    bson.D{{Key: "jobId", Value: 1}},
			Options: options.Index().SetUnique(true),
		},
		{
			// Compounding index for atomic queue locking
			Keys: bson.D{{Key: "status", Value: 1}, {Key: "priority", Value: -1}, {Key: "enqueuedAt", Value: 1}},
		},
	})
	if err != nil {
		return err
	}

	// 5. Execution history indexes
	historyCol := db.Collection("execution_history")
	_, err = historyCol.Indexes().CreateMany(ctx, []mongo.IndexModel{
		{
			Keys: bson.D{{Key: "jobId", Value: 1}},
		},
		{
			Keys: bson.D{{Key: "workerId", Value: 1}},
		},
		{
			Keys: bson.D{{Key: "taskId", Value: 1}},
		},
	})
	if err != nil {
		return err
	}

	// 6. Metrics collection TTL index (automatic cleanup after 30 days)
	metricsCol := db.Collection("metrics")
	ttlSeconds := int32(30 * 24 * 3600) // 30 Days in seconds
	_, err = metricsCol.Indexes().CreateOne(ctx, mongo.IndexModel{
		Keys:    bson.D{{Key: "timestamp", Value: 1}},
		Options: options.Index().SetExpireAfterSeconds(ttlSeconds),
	})
	if err != nil {
		return err
	}

	return nil
}
