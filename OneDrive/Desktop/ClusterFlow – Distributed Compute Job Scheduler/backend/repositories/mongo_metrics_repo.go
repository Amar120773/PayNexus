package repositories

import (
	"context"
	"time"
	"clusterflow/telemetry"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MongoMetricsRepository struct {
	collection *mongo.Collection
}

func NewMongoMetricsRepository(db *mongo.Database) telemetry.MetricsRepository {
	return &MongoMetricsRepository{
		collection: db.Collection("metrics"),
	}
}

func (r *MongoMetricsRepository) Insert(ctx context.Context, m *telemetry.MetricSnapshot) error {
	m.Timestamp = time.Now().UTC()
	_, err := r.collection.InsertOne(ctx, m)
	return err
}

func (r *MongoMetricsRepository) GetHistory(ctx context.Context, start, end time.Time) ([]telemetry.MetricSnapshot, error) {
	var list []telemetry.MetricSnapshot
	filter := bson.M{
		"timestamp": bson.M{
			"$gte": start,
			"$lte": end,
		},
	}
	opts := options.Find().SetSort(bson.D{{Key: "timestamp", Value: 1}})

	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	for cursor.Next(ctx) {
		var m telemetry.MetricSnapshot
		if err := cursor.Decode(&m); err != nil {
			return nil, err
		}
		list = append(list, m)
	}
	return list, nil
}
