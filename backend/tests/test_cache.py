import os
import shutil
import tempfile
import unittest
import time
import json
from cache import DictionaryCache


class TestDictionaryCache(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_cache_dir = tempfile.mkdtemp()
        self.cache = DictionaryCache(name="test_cache", expiration_time=1, cache_dir=self.test_cache_dir)

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_cache_dir)

    def test_set_and_get(self):
        # Test setting and getting a value
        test_key = "test_key"
        test_value = {"name": "Test Value", "data": 123}
        
        self.cache.set(test_key, test_value)
        retrieved_value = self.cache.get(test_key)
        
        self.assertEqual(retrieved_value, test_value)
        
    def test_expiration(self):
        # Test that values expire after the expiration time
        test_key = "expiring_key"
        test_value = {"name": "Expiring Value", "data": 456}
        
        self.cache.set(test_key, test_value)
        # Verify the value is there initially
        self.assertEqual(self.cache.get(test_key), test_value)
        
        # Wait for expiration
        time.sleep(1.5)
        
        # After expiration, should return None
        self.assertIsNone(self.cache.get(test_key))
    
    def test_clear(self):
        # Test clearing the cache
        test_key1 = "key1"
        test_key2 = "key2"
        test_value = {"data": "test"}
        
        self.cache.set(test_key1, test_value)
        self.cache.set(test_key2, test_value)
        
        # Verify values are there
        self.assertEqual(self.cache.get(test_key1), test_value)
        self.assertEqual(self.cache.get(test_key2), test_value)
        
        # Clear the cache
        self.cache.clear()
        
        # Verify values are gone
        self.assertIsNone(self.cache.get(test_key1))
        self.assertIsNone(self.cache.get(test_key2))


if __name__ == "__main__":
    unittest.main()