package store

import (
	"testing"
)

func TestRedisCacheConfig(t *testing.T) {
	cfg := RedisConfig{
		Addr:     "localhost:6379",
		Password: "",
		DB:       0,
	}

	rc := NewRedisCache(cfg)
	if rc.addr != "localhost:6379" {
		t.Errorf("addr = %q", rc.addr)
	}
}

func TestRedisCacheFromEnv(t *testing.T) {
	t.Setenv("REDIS_ADDR", "redis:6379")
	t.Setenv("REDIS_PASSWORD", "secret")

	rc := NewRedisCacheFromEnv()
	if rc.addr != "redis:6379" {
		t.Errorf("addr = %q", rc.addr)
	}
	if rc.password != "secret" {
		t.Errorf("password = %q", rc.password)
	}
}
