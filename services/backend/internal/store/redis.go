package store

import (
	"context"
	"os"
	"time"

	"github.com/redis/go-redis/v9"
)

// RedisConfig holds connection parameters for Redis.
type RedisConfig struct {
	Addr     string
	Password string
	DB       int
}

// RedisCache implements Cache using Redis.
type RedisCache struct {
	client   *redis.Client
	addr     string
	password string
	db       int
}

// NewRedisCache creates a RedisCache with the given config.
func NewRedisCache(cfg RedisConfig) *RedisCache {
	return &RedisCache{
		addr:     cfg.Addr,
		password: cfg.Password,
		db:       cfg.DB,
	}
}

// NewRedisCacheFromEnv creates a RedisCache reading config from environment variables.
func NewRedisCacheFromEnv() *RedisCache {
	return &RedisCache{
		addr:     getEnv("REDIS_ADDR", "localhost:6379"),
		password: os.Getenv("REDIS_PASSWORD"),
	}
}

// Connect initializes the Redis client.
func (rc *RedisCache) Connect() {
	rc.client = redis.NewClient(&redis.Options{
		Addr:     rc.addr,
		Password: rc.password,
		DB:       rc.db,
	})
}

// Get retrieves a value from Redis.
func (rc *RedisCache) Get(key string) ([]byte, bool) {
	if rc.client == nil {
		return nil, false
	}
	val, err := rc.client.Get(context.Background(), key).Bytes()
	if err != nil {
		return nil, false
	}
	return val, true
}

// Set stores a value in Redis with a 5-minute TTL.
func (rc *RedisCache) Set(key string, value []byte) {
	if rc.client == nil {
		return
	}
	_ = rc.client.Set(context.Background(), key, value, 5*time.Minute).Err()
}

// Delete removes a value from Redis.
func (rc *RedisCache) Delete(key string) {
	if rc.client == nil {
		return
	}
	_ = rc.client.Del(context.Background(), key).Err()
}

// Close closes the Redis client.
func (rc *RedisCache) Close() error {
	if rc.client != nil {
		return rc.client.Close()
	}
	return nil
}
