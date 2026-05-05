import time
import hashlib
import json
import os
import shutil

class DictionaryCache:
    def __init__(self, name="default", expiration_time=300, cache_dir="/tmp/cache"):
        """
        Initialize the cache with a custom name, an optional expiration time (in seconds),
        and a directory to store cached data.
        """
        self.name = name
        self.cache = {}  # in-memory store
        self.expiration_time = expiration_time
        self.cache_dir = os.path.join(cache_dir, self.name)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_file_path(self, key):
        """
        Get the file path for a given cache key.
        """
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key):
        """
        Retrieve a cached response using a custom key if it exists and is not expired.
        """
        cache_file = self._get_cache_file_path(key)

        # 1) Try in-memory cache first
        entry = self.cache.get(key)
        if entry:
            if time.time() - entry['timestamp'] < self.expiration_time:
                return entry['response']
            else:
                # expired in memory: evict mem + disk
                del self.cache[key]
                try: os.remove(cache_file)
                except OSError: pass
                return None

        # 2) Fallback to disk-based cache
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cached_entry = json.load(f)
            if time.time() - cached_entry['timestamp'] < self.expiration_time:
                # populate memory for next time
                self.cache[key] = cached_entry
                return cached_entry['response']
            else:
                os.remove(cache_file)
        return None

    def set(self, key, response):
        """
        Cache a response using a custom key.
        """
        cache_file = self._get_cache_file_path(key)
        cached_entry = {
            'response': response,
            'timestamp': time.time()
        }
        # 1) write to disk
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(cached_entry, f)
        # 2) store in memory
        self.cache[key] = cached_entry

    def clear(self):
        """
        Clear the entire cache directory.
        """
        # 1) clear memory
        self.cache.clear()
        # 2) clear disk
        shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)


# Example usage
if __name__ == "__main__":
    # Create a cache instance
    cache = DictionaryCache(name="example_cache", expiration_time=10)

    # Set a value in the cache
    cache.set("user_123", {"name": "Alice", "age": 30})

    # Retrieve the value from the cache
    cached_value = cache.get("user_123")
    print("Cached Value:", cached_value)

    # Wait for 11 seconds (to simulate expiration)
    time.sleep(11)

    # Try retrieving the value again (should return None)
    expired_value = cache.get("user_123")
    print("Expired Value:", expired_value)

    # Clear the cache
    cache.clear()
