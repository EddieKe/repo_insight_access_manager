"""
platform_client.py

Core data access layer for the platform (formerly Azure DevOps).
Handles fetching workspaces, repositories, teams, members, and access reports.
"""

import os
import json
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Set
from dotenv import load_dotenv
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from cache import DictionaryCache
from settings_manager import get_env_or_config_value
from report_client import ReportApiClient
from report_parser import ReportDataParser

# ----------------------------------------------------------------------
# Directories and files
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
REPO_LIST_FILE = os.path.join(CACHE_DIR, 'repos_list.json')

# ----------------------------------------------------------------------
# Credentials
# ----------------------------------------------------------------------
load_dotenv()
ORG_URL = get_env_or_config_value("AZURE_DEVOPS_ORG_URL", "org_url")
API_TOKEN = get_env_or_config_value("AZURE_DEVOPS_PAT", "api_token")

# ----------------------------------------------------------------------
# Global connection objects
# ----------------------------------------------------------------------
connection = None
_core_client = None
_git_client = None
_graph_client = None
_report_client = None

# ----------------------------------------------------------------------
# Cache
# ----------------------------------------------------------------------
cache = DictionaryCache(CACHE_DIR, expiration_time=3600)   


def setup_connection():
    """Establish connection to the platform with current credentials."""
    global connection, _core_client, _git_client, _graph_client, _report_client
    if not ORG_URL or not API_TOKEN:
        print("Platform credentials not configured. Please use the configuration endpoint to set org_url and api_token.")
        return

    try:
        credentials = BasicAuthentication('', API_TOKEN)
        connection = Connection(base_url=ORG_URL, creds=credentials)
        _core_client = connection.clients.get_core_client()
        _git_client = connection.clients.get_git_client()
        _graph_client = connection.clients.get_graph_client()
        _report_client = ReportApiClient(ORG_URL, API_TOKEN)
    except Exception as e:
        print(f"Failed to connect to platform: {str(e)}")


def reload_platform_config():
    """Reload configuration and reset connection after changes."""
    global ORG_URL, API_TOKEN
    ORG_URL = get_env_or_config_value("AZURE_DEVOPS_ORG_URL", "org_url")
    API_TOKEN = get_env_or_config_value("AZURE_DEVOPS_PAT", "api_token")
    cache.clear()
    setup_connection()


# Initialize connection
setup_connection()


# ----------------------------------------------------------------------
# Repository registration (for background fetching)
# ----------------------------------------------------------------------
def _load_repo_list() -> List[str]:
    """Load list of registered repository IDs from disk."""
    if not os.path.exists(REPO_LIST_FILE):
        return []
    with open(REPO_LIST_FILE, 'r') as f:
        return json.load(f)


def _save_repo_list(repo_ids: List[str]) -> None:
    """Save list of registered repository IDs to disk."""
    with open(REPO_LIST_FILE, 'w') as f:
        json.dump(repo_ids, f)


def register_repo(repo_id: str) -> None:
    """Add a repository ID to the fetch list."""
    repos = set(_load_repo_list())
    repos.add(repo_id)
    _save_repo_list(list(repos))


def get_registered_repos() -> List[str]:
    """Return the list of repository IDs to fetch."""
    return _load_repo_list()


# ----------------------------------------------------------------------
# Workspaces (projects)
# ----------------------------------------------------------------------
def fetch_workspaces() -> List[Dict]:
    """Return a list of all workspaces in the organization."""
    cache_key = "workspaces_list"
    cached = cache.get(cache_key)
    if cached:
        return cached

    workspaces = []
    for p in _core_client.get_projects():
        workspaces.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'state': p.state,
            'visibility': p.visibility
        })
    cache.set(cache_key, workspaces)
    return workspaces


def fetch_code_repos(workspace_id: str) -> List[Dict]:
    """Return a list of code repositories inside the given workspace."""
    cache_key = f"repos_list_{workspace_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    repos = []
    for r in _git_client.get_repositories(project=workspace_id):
        repos.append({
            'id': r.id,
            'name': r.name,
            'url': r.web_url,
            'defaultBranch': r.default_branch
        })
    cache.set(cache_key, repos)
    return repos


# ----------------------------------------------------------------------
# Access reports (permissions)
# ----------------------------------------------------------------------
def fetch_access_report(workspace_id: str, repo_id: str = None, repo_name: str = None) -> Optional[Dict]:
    """Create and download an access report for a workspace (or a specific repository)."""
    cache_key = f"access_report_{workspace_id}_repo_{repo_id}" if repo_id else f"access_report_{workspace_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Choose resource type and ID
    if repo_id:
        resource_type = "Repo"
        resource_id = f"{workspace_id}/{repo_id}"
        resource_name = repo_name
    else:
        resource_type = "projectGit"
        resource_id = workspace_id
        resource_name = ""

    report_name = f"access_report_{workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    report = _report_client.create_report(
        report_name=report_name,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        descriptors=[]          # empty list means all users and groups
    )

    report_id = report.get("id")
    _report_client.wait_for_completion(report_id)
    report_data = _report_client.download_report(report_id)

    cache.set(cache_key, report_data)
    return report_data


def parse_access_report(report_data: Dict, workspace_id: str = None, repo_id: str = None) -> Optional[Dict]:
    """Parse raw report data into structured group and user information."""
    cache_key = f"parsed_access_{workspace_id}_{repo_id}" if repo_id else f"parsed_access_{workspace_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    parser = ReportDataParser(report_data)
    parsed = parser.parse()
    cache.set(cache_key, parsed)
    return parsed


def fetch_repo_access(repo_id: str) -> Optional[Dict]:
    """Return access rights for a specific repository."""
    # Find the workspace (project) containing this repository
    for ws in fetch_workspaces():
        repos = fetch_code_repos(ws['id'])
        for repo in repos:
            if repo['id'] == repo_id:
                workspace_id = ws['id']
                repo_name = repo['name']
                break
        else:
            continue
        break
    else:
        return None

    raw_report = fetch_access_report(workspace_id, repo_id, repo_name)
    if not raw_report:
        return None
    parsed = parse_access_report(raw_report, workspace_id, repo_id)
    return parsed["repository_permissions"].get(repo_name, {})


def fetch_teams(workspace_id: str) -> Optional[Dict]:
    """Return all security teams (groups) inside a workspace."""
    raw_report = fetch_access_report(workspace_id)
    if not raw_report:
        return None
    parsed = parse_access_report(raw_report, workspace_id)
    return parsed.get("groups", {})


def fetch_team_members(team_descriptor: str) -> Optional[List[Dict]]:
    """
    Return all members of a security team, including members of nested teams.
    """
    cache_key = f"team_members_{team_descriptor}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    members = _fetch_team_members_uncached(team_descriptor)
    cache.set(cache_key, members)
    return members


def _fetch_team_members_uncached(descriptor: str, visited: Optional[Set[str]] = None) -> List[Dict]:
    """Recursively fetch members of a team, following nested teams."""
    if visited is None:
        visited = set()
    membership_refs = _graph_client.list_memberships(subject_descriptor=descriptor, direction='down')
    members = []
    for membership in membership_refs:
        member_desc = membership.as_dict()['member_descriptor']
        if member_desc in visited:
            continue
        visited.add(member_desc)

        if member_desc.startswith("vssgp."):   # group descriptor
            members.extend(_fetch_team_members_uncached(member_desc, visited))
        else:
            user = fetch_user_details(member_desc)
            if user:
                members.append(user)
    return members


def fetch_user_details(user_descriptor: str) -> Optional[Dict]:
    """Return details of a user by descriptor."""
    cache_key = f"user_{user_descriptor}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    if user_descriptor.startswith("vssgp."):
        return None

    user = _graph_client.get_user(user_descriptor).as_dict()
    if user:
        cache.set(cache_key, user)
    return user


def fetch_user_rights(user_descriptor: str) -> Optional[Dict]:
    """Return all access rights for a user across all workspaces."""
    if not user_descriptor:
        return None
    result = {}
    for ws in fetch_workspaces():
        ws_id = ws['id']
        raw_report = fetch_access_report(ws_id)
        if not raw_report:
            continue
        parsed = parse_access_report(raw_report, ws_id)
        # Find user ID from descriptor
        user_id = None
        for uid, info in parsed["users"].items():
            if info["descriptor"] == user_descriptor:
                user_id = uid
                break
        if user_id and user_id in parsed["user_permissions"]:
            result[ws_id] = parsed["user_permissions"][user_id]
    return result


def fetch_repo_members(repo_id: str) -> List[Dict]:
    """Return all users who have direct access rights to a repository."""
    # Find workspace and repo name
    for ws in fetch_workspaces():
        repos = fetch_code_repos(ws['id'])
        for repo in repos:
            if repo['id'] == repo_id:
                workspace_id = ws['id']
                repo_name = repo['name']
                break
        else:
            continue
        break
    else:
        return []

    raw_report = fetch_access_report(workspace_id, repo_id, repo_name)
    if not raw_report:
        return []
    parsed = parse_access_report(raw_report, workspace_id, repo_id)

    members = []
    for user_id, perms_dict in parsed.get("user_permissions", {}).items():
        # Check if user has any direct permission for this repository
        direct_perms = perms_dict.get("direct", [])
        if direct_perms:
            user_info = parsed["users"].get(user_id, {})
            descriptor = user_info.get("descriptor")
            if descriptor:
                details = fetch_user_details(descriptor) or {}
                role = "Admin" if any(p.get('permission_name') == 'GenericAdmin' and
                                       p.get('effective_permission') in ('Allow', 'InheritedAllow')
                                       for p in direct_perms) else "Contributor"
                members.append({
                    'descriptor': descriptor,
                    'display_name': details.get('display_name', user_info.get('display_name', 'Unknown')),
                    'mail_address': details.get('mail_address', ''),
                    'origin': details.get('origin', 'Azure DevOps'),
                    'role': role
                })
    return members


def fetch_user_repo_rights(user_descriptor: str, repo_id: str) -> Optional[Dict]:
    """Return specific access rights of a user for a given repository."""
    # Find workspace and repo name
    for ws in fetch_workspaces():
        repos = fetch_code_repos(ws['id'])
        for repo in repos:
            if repo['id'] == repo_id:
                workspace_id = ws['id']
                repo_name = repo['name']
                break
        else:
            continue
        break
    else:
        return None

    raw_report = fetch_access_report(workspace_id, repo_id, repo_name)
    if not raw_report:
        return None
    parsed = parse_access_report(raw_report, workspace_id, repo_id)

    # Find user ID from descriptor
    user_id = None
    for uid, info in parsed["users"].items():
        if info["descriptor"] == user_descriptor:
            user_id = uid
            break
    if not user_id:
        return None

    user_info = parsed["users"].get(user_id, {})
    details = fetch_user_details(user_descriptor) or {}
    display_name = details.get('principalName') or details.get('display_name') or user_info.get('display_name', 'Unknown')

    return {
        'user': {
            'id': user_id,
            'descriptor': user_descriptor,
            'displayName': display_name
        },
        'repository': {
            'id': repo_id,
            'name': repo_name,
            'projectId': workspace_id
        },
        'permissions': parsed["user_permissions"].get(user_id, {})
    }
