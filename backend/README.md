# Azure DevOps Dashboard - Backend

The backend component of the Azure DevOps Repository Dashboard provides a REST API for retrieving and managing data from Azure DevOps. It uses the Azure DevOps REST API and SDK to fetch information about projects, repositories, security groups, and permissions.

## Architecture

The backend is built with Python and Flask, utilizing several key components:

- **API Layer (`api.py`)**: Exposes REST endpoints for the frontend to consume
- **Data Access Layer (`azure_data.py`)**: Handles interactions with the Azure DevOps API
- **Caching System (`cache.py`)**: Improves performance by caching responses
- **Configuration Management (`config_manager.py`)**: Manages Azure DevOps connection settings
- **Excel Export (`excel_exporter.py`)**: Generates Excel reports from permission data
- **Permission Reports (`permissions_report_*.py`)**: Specialized classes for handling permission data

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | GET | Get all projects |
| `/api/projects/<project_id>` | GET | Get details for a specific project |
| `/api/projects/<project_id>/repositories` | GET | Get repositories for a project |
| `/api/projects/<project_id>/groups` | GET | Get security groups for a project |
| `/api/repositories/<repo_id>/permissions` | GET | Get permissions for a repository |
| `/api/groups/<descriptor>/members` | GET | Get members of a security group |
| `/api/users/<descriptor>/permissions` | GET | Get permissions for a user |
| `/api/repositories/<repo_id>/members` | GET | Get members with direct access to a repository |
| `/api/projects/<project_id>/export-excel` | GET | Export permissions to Excel |
| `/api/config/azure-devops` | GET | Get the current Azure DevOps configuration |
| `/api/config/azure-devops` | POST | Update Azure DevOps configuration |
| `/api/cache/clear` | POST | Clear all cached data |

## Caching System

The backend includes a sophisticated caching system to improve performance:

- In-memory cache for fast access
- Disk-based cache for persistence between server restarts
- Configurable expiration times
- Cache clearing endpoint for refreshing data

## Configuration

The application requires the following configuration:

1. **Azure DevOps Organization URL**: The URL of your Azure DevOps organization
2. **Personal Access Token (PAT)**: A token with sufficient permissions to read projects, repositories, and permissions

These settings can be configured through the frontend UI or by directly modifying the `config.json` file.

## Development

### Prerequisites

- Python 3.8+
- Required Python packages listed in `requirements.txt`

### Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```
   python api.py
   ```

### Key Files

- `api.py`: Flask API endpoints and routing
- `azure_data.py`: Core business logic for fetching Azure DevOps data
- `cache.py`: Caching implementation for API responses
- `config_manager.py`: Configuration management utilities
- `permissions_report_client.py`: Client for the Azure DevOps Permissions Report API
- `permissions_report_parser.py`: Parser for Azure DevOps permission data
- `excel_exporter.py`: Excel report generation functionality