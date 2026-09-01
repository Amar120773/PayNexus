package repositories

import (
	"context"
	"time"
	"clusterflow/workers"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

type MongoWorkerRepository struct {
	collection *mongo.Collection
}

func NewMongoWorkerRepository(db *mongo.Database) workers.WorkerRepository {
	return &MongoWorkerRepository{
		collection: db.Collection("workers"),
	}
}

func (r *MongoWorkerRepository) Create(ctx context.Context, worker *workers.WorkerNode) error {
	_, err := r.collection.InsertOne(ctx, worker)
	return err
}

func (r *MongoWorkerRepository) FindByID(ctx context.Context, id string) (*workers.WorkerNode, error) {
	var worker workers.WorkerNode
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&worker)
	if err != nil {
		return nil, err
	}
	return &worker, nil
}

func (r *MongoWorkerRepository) FindAll(ctx context.Context) ([]workers.WorkerNode, error) {
	var list []workers.WorkerNode
	cursor, err := r.collection.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	for cursor.Next(ctx) {
		var node workers.WorkerNode
		if err := cursor.Decode(&node); err != nil {
			return nil, err
		}
		list = append(list, node)
	}
	return list, nil
}

func (r *MongoWorkerRepository) Update(ctx context.Context, worker *workers.WorkerNode) error {
	_, err := r.collection.ReplaceOne(ctx, bson.M{"_id": worker.ID}, worker)
	return err
}

func (r *MongoWorkerRepository) Delete(ctx context.Context, id string) error {
	_, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	return err
}

func (r *MongoWorkerRepository) UpdateHeartbeat(ctx context.Context, id string, stats workers.ResourceStats, runningTasks []string) error {
	update := bson.M{
		"$set": bson.M{
			"resources":     stats,
			"runningTasks":  runningTasks,
			"lastHeartbeat": time.Now().UTC(),
			"state":         workers.StateActive,
		},
	}
	_, err := r.collection.UpdateOne(ctx, bson.M{"_id": id}, update)
	return err
}
