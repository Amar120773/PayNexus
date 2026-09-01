package repositories

import (
	"context"
	"clusterflow/jobs"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MongoHistoryRepository struct {
	collection *mongo.Collection
}

func NewMongoHistoryRepository(db *mongo.Database) jobs.HistoryRepository {
	return &MongoHistoryRepository{
		collection: db.Collection("execution_history"),
	}
}

func (r *MongoHistoryRepository) Save(ctx context.Context, record *jobs.TaskExecutionRecord) error {
	record.DurationMs = record.FinishedAt.Sub(record.StartedAt).Milliseconds()
	_, err := r.collection.InsertOne(ctx, record)
	return err
}

func (r *MongoHistoryRepository) GetByJob(ctx context.Context, jobID string) ([]jobs.TaskExecutionRecord, error) {
	var list []jobs.TaskExecutionRecord
	filter := bson.M{"jobId": jobID}
	opts := options.Find().SetSort(bson.D{{Key: "startedAt", Value: 1}})

	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	for cursor.Next(ctx) {
		var record jobs.TaskExecutionRecord
		if err := cursor.Decode(&record); err != nil {
			return nil, err
		}
		list = append(list, record)
	}
	return list, nil
}

func (r *MongoHistoryRepository) GetByWorker(ctx context.Context, workerID string) ([]jobs.TaskExecutionRecord, error) {
	var list []jobs.TaskExecutionRecord
	filter := bson.M{"workerId": workerID}
	opts := options.Find().SetSort(bson.D{{Key: "finishedAt", Value: -1}})

	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	for cursor.Next(ctx) {
		var record jobs.TaskExecutionRecord
		if err := cursor.Decode(&record); err != nil {
			return nil, err
		}
		list = append(list, record)
	}
	return list, nil
}
