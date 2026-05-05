"""
excel_generator.py

Generate Excel reports (XLSX) from platform access data.
Creates a comprehensive sheet with all user and group permissions.
"""

from platform_client import (
    fetch_workspaces,
    fetch_code_repos,
    fetch_teams,
    fetch_user_details,
    fetch_access_report,
    parse_access_report
)
import pandas as pd


def export_access_to_excel(output_file: str, workspace_id: str = None) -> None:
    """
    Export all access rights for a workspace (or all if workspace_id is None) to an Excel file.

    Args:
        output_file: Path where the Excel file will be saved.
        workspace_id: Optional workspace identifier. If provided, only that workspace is exported.
    """
    all_rows = []

    workspaces = fetch_workspaces()
    if workspace_id:
        workspaces = [w for w in workspaces if w['id'] == workspace_id or w['name'] == workspace_id]
        if not workspaces:
            return

    for ws in workspaces:
        ws_id = ws['id']
        ws_name = ws['name']

        # Export workspace‑level permissions
        ws_report = fetch_access_report(ws_id)
        if ws_report:
            parsed_ws = parse_access_report(ws_report, ws_id)
            _add_workspace_level_rows(parsed_ws, ws_name, ws_id, all_rows)

        # Export each repository inside the workspace
        repos = fetch_code_repos(ws_id)
        for repo in repos:
            repo_id = repo['id']
            repo_name = repo['name']

            repo_report = fetch_access_report(ws_id, repo_id, repo_name)
            if not repo_report:
                continue
            parsed_repo = parse_access_report(repo_report, ws_id, repo_id)
            _add_repository_level_rows(parsed_repo, ws_name, ws_id, repo_name, repo_id, all_rows)

    if all_rows:
        df = pd.DataFrame(all_rows)
        # Write with basic Excel engine (no styling dependencies)
        df.to_excel(output_file, index=False)
        print(f"Access report exported to {output_file}")
    else:
        print("No access data found to export.")


def _add_workspace_level_rows(parsed: dict, ws_name: str, ws_id: str, rows: list) -> None:
    """Add rows for workspace‑level permissions (users and groups)."""
    # User permissions at workspace level
    for user_id, perms_map in parsed.get("user_permissions", {}).items():
        user_info = parsed["users"].get(user_id, {})
        descriptor = user_info.get("descriptor")
        display_name = _get_display_name(descriptor, user_info.get("display_name", "N/A"))

        for perm in perms_map.get("direct", []):
            rows.append({
                'Workspace Name': ws_name,
                'Workspace ID': ws_id,
                'Repository Name': 'N/A (Workspace Level)',
                'Repository ID': 'N/A (Workspace Level)',
                'Type': 'User',
                'Name': display_name,
                'Descriptor': descriptor,
                'Permission': perm.get('permission_name', 'N/A'),
                'Allowed': perm.get('effective_permission') in ('Allow', 'InheritedAllow'),
                'Denied': perm.get('effective_permission') in ('Denied', 'InheritedDenied'),
                'Inherited': perm.get('is_inherited', False)
            })

    # Group permissions at workspace level
    for group_id, perms_list in parsed.get("group_permissions", {}).items():
        group_info = parsed["groups"].get(group_id, {})
        group_name = group_info.get("display_name", "N/A")
        group_descriptor = group_info.get("descriptor")

        for perm in perms_list:
            rows.append({
                'Workspace Name': ws_name,
                'Workspace ID': ws_id,
                'Repository Name': 'N/A (Workspace Level)',
                'Repository ID': 'N/A (Workspace Level)',
                'Type': 'Group',
                'Name': group_name,
                'Descriptor': group_descriptor,
                'Permission': perm.get('permission_name', 'N/A'),
                'Allowed': perm.get('effective_permission') in ('Allow', 'InheritedAllow'),
                'Denied': perm.get('effective_permission') in ('Denied', 'InheritedDenied'),
                'Inherited': perm.get('is_inherited', False)
            })


def _add_repository_level_rows(parsed: dict, ws_name: str, ws_id: str,
                               repo_name: str, repo_id: str, rows: list) -> None:
    """Add rows for repository‑level permissions (users and groups)."""
    # User permissions
    for user_id, perms_map in parsed.get("user_permissions", {}).items():
        user_info = parsed["users"].get(user_id, {})
        descriptor = user_info.get("descriptor")
        display_name = _get_display_name(descriptor, user_info.get("display_name", "N/A"))

        for perm in perms_map.get("direct", []):
            rows.append({
                'Workspace Name': ws_name,
                'Workspace ID': ws_id,
                'Repository Name': repo_name,
                'Repository ID': repo_id,
                'Type': 'User',
                'Name': display_name,
                'Descriptor': descriptor,
                'Permission': perm.get('permission_name', 'N/A'),
                'Allowed': perm.get('effective_permission') in ('Allow', 'InheritedAllow'),
                'Denied': perm.get('effective_permission') in ('Denied', 'InheritedDenied'),
                'Inherited': perm.get('is_inherited', False)
            })

    # Group permissions
    for group_id, perms_list in parsed.get("group_permissions", {}).items():
        group_info = parsed["groups"].get(group_id, {})
        group_name = group_info.get("display_name", "N/A")
        group_descriptor = group_info.get("descriptor")

        for perm in perms_list:
            rows.append({
                'Workspace Name': ws_name,
                'Workspace ID': ws_id,
                'Repository Name': repo_name,
                'Repository ID': repo_id,
                'Type': 'Group',
                'Name': group_name,
                'Descriptor': group_descriptor,
                'Permission': perm.get('permission_name', 'N/A'),
                'Allowed': perm.get('effective_permission') in ('Allow', 'InheritedAllow'),
                'Denied': perm.get('effective_permission') in ('Denied', 'InheritedDenied'),
                'Inherited': perm.get('is_inherited', False)
            })


def _get_display_name(descriptor: str, fallback: str) -> str:
    """Try to fetch a better display name from user details."""
    details = fetch_user_details(descriptor) if descriptor else None
    if details:
        return details.get('principalName') or details.get('display_name') or fallback
    return fallback
