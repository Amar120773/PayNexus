package repositories

import (
	"context"
	"time"
	"clusterflow/scheduler"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MongoQueueRepository struct {
	collection *mongo.Collection
}

func NewMongoQueueRepository(db *mongo.Database) scheduler.QueueRepository {
	return &MongoQueueRepository{
		collection: db.Collection("queue"),
	}
}

func (r *MongoQueueRepository) Enqueue(ctx context.Context, item *scheduler.PersistentQueueItem) error {
	item.EnqueuedAt = time.Now().UTC()
	item.Status = scheduler.QueueStateWaiting
	_, err := r.collection.InsertOne(ctx, item)
	return err
}

func (r *MongoQueueRepository) Dequeue(ctx context.Context, jobID string) error {
	_, err := r.collection.DeleteOne(ctx, bson.M{"jobId": jobID})
	return err
}

func (r *MongoQueueRepository) ListWaiting(ctx context.Context) ([]scheduler.PersistentQueueItem, error) {
	var list []scheduler.PersistentQueueItem
	query := bson.M{"status": scheduler.QueueStateWaiting}
	opts := options.Find().SetSort(bson.D{{Key: "priority", Value: -1}, {Key: "enqueuedAt", Value: 1}})
	
	cursor, err := r.collection.Find(ctx, query, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	for cursor.Next(ctx) {
		var item scheduler.PersistentQueueItem
		if err := cursor.Decode(&item); err != nil {
			return nil, err
		}
		list = append(list, item)
	}
	return list, nil
}

func (r *MongoQueueRepository) LockNextItem(ctx context.Context, lockerID string) (*scheduler.PersistentQueueItem, error) {
	// atomatically find next WAITING task, sort by priority DESC, enqueue ASC, update status to LOCKED
	filter := bson.M{"status": scheduler.QueueStateWaiting}
	update := bson.M{
		"$set": bson.M{
			"status":   scheduler.QueueStateLocked,
			"lockedBy": lockerID,
			"lockedAt": time.Now().UTC(),
		},
	}
	opts := options.FindOneAndUpdate().
		SetSort(bson.D{{Key: "priority", Value: -1}, {Key: "enqueuedAt", Value: 1}}).
		SetReturnDocument(options.After)

	var item scheduler.PersistentQueueItem
	err := r.collection.FindOneAndUpdate(ctx, filter, update, opts).Decode(&item)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, nil // No jobs waiting
		}
		return nil, err
	}
	return &item, nil
}

func (r *MongoQueueRepository) ReleaseLock(ctx context.Context, jobID string) error {
	filter := bson.M{"jobId": jobID, "status": scheduler.QueueStateLocked}
	update := bson.M{
		"$set": bson.M{
			"status": scheduler.QueueStateWaiting,
		},
		"$unset": bson.M{
			"lockedBy": "",
			"lockedAt": "",
		},
	}
	_, err := r.collection.UpdateOne(ctx, filter, update)
	return err
}
