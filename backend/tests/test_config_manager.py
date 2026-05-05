import os
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch
from config_manager import save_azure_devops_config, get_azure_devops_config, get_env_or_config_value


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "config.json")
        
        # Setup a patch for the config file path
        self.patcher = patch('config_manager.CONFIG_FILE', self.config_path)
        self.mock_config_file = self.patcher.start()
    
    def tearDown(self):
        # Stop the patcher
        self.patcher.stop()
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_save_and_get_config(self):
        # Test saving and retrieving configuration
        test_org_url = "https://dev.azure.com/test-org"
        test_pat = "test-pat-token"
        
        # Save the config
        result = save_azure_devops_config(test_org_url, test_pat)
        self.assertTrue(result)
        
        # Get the config
        config = get_azure_devops_config()
        
        self.assertEqual(config["org_url"], test_org_url)
        self.assertEqual(config["pat"], test_pat)
    
    @patch.dict(os.environ, {"AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/env-org"})
    def test_get_env_or_config_value_from_env(self):
        # Test getting a value from environment variable
        value = get_env_or_config_value("AZURE_DEVOPS_ORG_URL", "org_url")
        self.assertEqual(value, "https://dev.azure.com/env-org")
    
    def test_get_env_or_config_value_from_config(self):
        # Save a config value
        save_azure_devops_config("https://dev.azure.com/config-org", "config-pat")
        
        # Test getting a value from config file
        # (assuming no AZURE_DEVOPS_ORG_URL env var is set)
        with patch.dict(os.environ, {}, clear=True):
            value = get_env_or_config_value("AZURE_DEVOPS_ORG_URL", "org_url")
            self.assertEqual(value, "https://dev.azure.com/config-org")


if __name__ == "__main__":
    unittest.main()