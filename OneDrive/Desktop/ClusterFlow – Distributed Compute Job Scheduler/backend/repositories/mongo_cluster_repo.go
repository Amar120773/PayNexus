package repositories

import (
	"context"
	"clusterflow/cluster"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

type MongoClusterRepository struct {
	collection *mongo.Collection
}

func NewMongoClusterRepository(db *mongo.Database) cluster.Repository {
	return &MongoClusterRepository{
		collection: db.Collection("clusters"),
	}
}

func (r *MongoClusterRepository) Get(ctx context.Context, id string) (*cluster.Cluster, error) {
	var c cluster.Cluster
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&c)
	if err != nil {
		return nil, err
	}
	return &c, nil
}

func (r *MongoClusterRepository) Update(ctx context.Context, c *cluster.Cluster) error {
	_, err := r.collection.ReplaceOne(ctx, bson.M{"_id": c.ID}, c)
	return err
}
