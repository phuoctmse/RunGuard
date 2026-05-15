import time

import pytest

from reasoner.cache import PromptCache


def test_cache_hit():
    cache = PromptCache()
    cache.set("PodCrashLooping", {"logs": "OOMKilled"}, "cached result")
    result = cache.get("PodCrashLooping", {"logs": "OOMKilled"})
    assert result == "cached result"


def test_cache_miss():
    cache = PromptCache()
    result = cache.get("UnknownAlert", {})
    assert result is None


def test_cache_expiry():
    cache = PromptCache(ttl_seconds=0.1)
    cache.set("test", {"key": "value"}, "result")
    time.sleep(0.2)
    result = cache.get("test", {"key": "value"})
    assert result is None


def test_cache_different_evidence():
    cache = PromptCache()
    cache.set("PodCrashLooping", {"logs": "OOMKilled"}, "result1")
    result = cache.get("PodCrashLooping", {"logs": "different logs"})
    assert result is None