package resilience

import "time"

func Retry(attempts int, delay time.Duration, fn func() error) error {
	var err error
	for i := 0; i < attempts; i++ {
		if err = fn(); err == nil {
			return nil
		}
		if i < attempts-1 {
			time.Sleep(delay * time.Duration(1<<i))
		}
	}
	return err
}
