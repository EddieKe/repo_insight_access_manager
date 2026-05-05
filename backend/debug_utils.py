"""Utility functions for debugging Azure DevOps data"""
import json

def print_report_structure(parsed_report, project_id, repo_id=None):
    """Print the structure of a parsed permissions report to help debugging"""
    print(f"\n=== Report Structure for Project {project_id} Repo {repo_id} ===")
    
    # Print top-level keys
    print(f"Top-level keys: {list(parsed_report.keys())}")
    
    # Check permissions array
    permissions = parsed_report.get("permissions", [])
    print(f"Permissions count: {len(permissions)}")
    if permissions and len(permissions) > 0:
        print("First permission entry:")
        print(json.dumps(permissions[0], indent=2))
    
    # Check users
    users = parsed_report.get("users", {})
    print(f"Users count: {len(users)}")
    if users:
        print("First user entry:")
        user_id = next(iter(users.keys()), None)
        if user_id:
            print(json.dumps({user_id: users[user_id]}, indent=2))
    
    # Check groups
    groups = parsed_report.get("groups", {})
    print(f"Groups count: {len(groups)}")
    if groups:
        print("First group entry:")
        group_id = next(iter(groups.keys()), None)
        if group_id:
            print(json.dumps({group_id: groups[group_id]}, indent=2))
    
    print("=== End of Report Structure ===\n")

# Then in azure_data.py, import and use this:
# from debug_utils import print_report_structure
# And add before processing the permissions:
# print_report_structure(parsed_report, project_id, repo_id)
