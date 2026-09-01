package repositories

import (
	"context"
	"clusterflow/jobs"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MongoJobRepository struct {
	collection *mongo.Collection
}

func NewMongoJobRepository(db *mongo.Database) jobs.JobRepository {
	return &MongoJobRepository{
		collection: db.Collection("jobs"),
	}
}

func (r *MongoJobRepository) Create(ctx context.Context, job *jobs.Job) error {
	_, err := r.collection.InsertOne(ctx, job)
	return err
}

func (r *MongoJobRepository) FindByID(ctx context.Context, id string) (*jobs.Job, error) {
	var job jobs.Job
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&job)
	if err != nil {
		return nil, err
	}
	return &job, nil
}

func (r *MongoJobRepository) FindAll(ctx context.Context, filter map[string]interface{}) ([]jobs.Job, error) {
	var jobsList []jobs.Job
	query := bson.M{}
	for k, v := range filter {
		query[k] = v
	}

	opts := options.Find().SetSort(bson.D{{Key: "priority", Value: -1}, {Key: "createdAt", Value: 1}})
	cursor, err := r.collection.Find(ctx, query, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	for cursor.Next(ctx) {
		var job jobs.Job
		if err := cursor.Decode(&job); err != nil {
			return nil, err
		}
		jobsList = append(jobsList, job)
	}

	if err := cursor.Err(); err != nil {
		return nil, err
	}

	return jobsList, nil
}

func (r *MongoJobRepository) Update(ctx context.Context, job *jobs.Job) error {
	_, err := r.collection.ReplaceOne(ctx, bson.M{"_id": job.ID}, job)
	return err
}

func (r *MongoJobRepository) Delete(ctx context.Context, id string) error {
	_, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	return err
}
