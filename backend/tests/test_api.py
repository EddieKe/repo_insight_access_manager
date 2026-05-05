import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Mock azure_data.setup_connection before importing api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
with patch('azure_data.setup_connection'):
    from api import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('api.get_projects')
    def test_list_projects(self, mock_get_projects):
        # Mock the return value
        mock_projects = [
            {"id": "project1", "name": "Project 1", "description": "Test Project 1", "state": "wellFormed", "visibility": "private"},
            {"id": "project2", "name": "Project 2", "description": "Test Project 2", "state": "wellFormed", "visibility": "public"}
        ]
        mock_get_projects.return_value = mock_projects
        
        # Make the request
        response = self.app.get('/api/projects')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, mock_projects)
        
        # Verify the mock was called
        mock_get_projects.assert_called_once()

    @patch('api.get_repositories')
    def test_list_repos(self, mock_get_repositories):
        # Mock the return value
        mock_repos = [
            {"id": "repo1", "name": "Repo 1", "url": "https://dev.azure.com/org/project/repo1", "defaultBranch": "refs/heads/main"},
            {"id": "repo2", "name": "Repo 2", "url": "https://dev.azure.com/org/project/repo2", "defaultBranch": "refs/heads/main"}
        ]
        mock_get_repositories.return_value = mock_repos
        
        # Make the request
        response = self.app.get('/api/projects/project1/repositories')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, mock_repos)
        
        # Verify the mock was called
        mock_get_repositories.assert_called_once_with("project1")

    @patch('api.cache')
    def test_clear_cache(self, mock_cache):
        # Setup the mock
        mock_cache.clear = MagicMock()
        
        # Make the request
        response = self.app.post('/api/cache/clear')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "Cache cleared"})
        
        # Verify the mock was called
        mock_cache.clear.assert_called_once()

    @patch('api.get_azure_devops_config')
    def test_get_config(self, mock_get_config):
        # Mock the return value
        mock_config = {
            "org_url": "https://dev.azure.com/test-org",
            "pat": "test-pat-token"
        }
        mock_get_config.return_value = mock_config
        
        # Make the request
        response = self.app.get('/api/config/azure-devops')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # PAT should be masked in the response
        self.assertEqual(data["org_url"], mock_config["org_url"])
        self.assertEqual(data["pat"], "********")


if __name__ == '__main__':
    unittest.main()