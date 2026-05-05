"""
report_parser.py

Parser for raw platform access report JSON data.
Converts the raw report into a structured form with groups, users, permissions,
and repository‑organized access.
"""

import json
import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any


class ReportDataParser:
    """
    Parses the JSON output of a platform access report into a structured format.
    """

    def __init__(self, json_data):
        """Initialize with either a JSON string or a pre‑parsed dict."""
        if isinstance(json_data, str):
            parsed_json = json.loads(json_data)
            self.data = parsed_json.get("PermissionsReport", [])
        else:
            self.data = json_data

        self.groups = {}
        self.users = {}
        self.group_memberships = defaultdict(set)
        self.group_permissions = defaultdict(list)
        self.repository_permissions = defaultdict(lambda: {"users": {}, "groups": {}})
        self.user_permissions = defaultdict(list)

    def parse(self) -> Dict[str, Any]:
        """Main entry point: process all entries and return structured output."""
        for entry in self.data:
            self._process_entry(entry)

        return self._build_output()

    def _process_entry(self, entry: Dict[str, Any]) -> None:
        """Process a single entry from the report."""
        descriptor = entry.get('Descriptor', '')
        principal_id = entry.get('Id', '')
        account_name = entry.get('AccountName', '')
        display_name = entry.get('DisplayName', '')
        permissions = entry.get('Permissions', [])
        resource = entry.get('Resource', {})

        is_group = descriptor.startswith('vssgp.')
        if is_group:
            self._process_group(principal_id, descriptor, account_name, display_name, permissions, resource)
        else:
            self._process_user(principal_id, descriptor, account_name, display_name, permissions, resource)

    def _process_group(self, group_id: str, descriptor: str, account_name: str,
                       display_name: str, permissions: List[Dict], resource: Dict) -> None:
        """Store group information and its permissions."""
        # Determine group type by name
        group_type = 'group'
        if 'administrators' in display_name.lower():
            group_type = 'admin_group'
        elif 'contributors' in display_name.lower():
            group_type = 'contributor_group'
        elif 'readers' in display_name.lower():
            group_type = 'reader_group'

        self.groups[group_id] = {
            'id': group_id,
            'descriptor': descriptor,
            'account_name': account_name,
            'display_name': display_name,
            'group_type': group_type
        }

        for perm in permissions:
            perm_data = {
                'permission_name': perm.get('PermissionName', 'Unknown'),
                'effective_permission': perm.get('EffectivePermission', 'Unknown'),
                'is_inherited': perm.get('IsPermissionInherited', False),
                'resource': resource
            }
            self.group_permissions[group_id].append(perm_data)

            # Also add to repository index
            repo_name = resource.get('ResourceName', 'Unknown')
            self.repository_permissions[repo_name]['groups'].setdefault(group_id, []).append(perm_data)

    def _process_user(self, user_id: str, descriptor: str, account_name: str,
                      display_name: str, permissions: List[Dict], resource: Dict) -> None:
        """Store user information and its permissions."""
        user_type = 'service_account' if descriptor.startswith('svc.') else 'azure_ad_user'
        self.users[user_id] = {
            'id': user_id,
            'descriptor': descriptor,
            'account_name': account_name,
            'display_name': display_name,
            'user_type': user_type
        }

        for perm in permissions:
            perm_data = {
                'permission_name': perm.get('PermissionName', 'Unknown'),
                'effective_permission': perm.get('EffectivePermission', 'Unknown'),
                'is_inherited': perm.get('IsPermissionInherited', False),
                'resource': resource
            }
            self.user_permissions[user_id].append(perm_data)

            # Also add to repository index
            repo_name = resource.get('ResourceName', 'Unknown')
            self.repository_permissions[repo_name]['users'].setdefault(user_id, []).append(perm_data)

            if perm_data['is_inherited']:
                self._infer_group_membership(user_id, perm_data)

    def _infer_group_membership(self, user_id: str, perm_data: Dict) -> None:
        """Try to guess which group gave an inherited permission."""
        for group_id, group_perms in self.group_permissions.items():
            for gp in group_perms:
                if (gp['permission_name'] == perm_data['permission_name'] and
                    gp['effective_permission'] == perm_data['effective_permission']):
                    self.group_memberships[user_id].add(group_id)

    def _build_output(self) -> Dict[str, Any]:
        """Assemble final output structure."""
        group_memberships_list = {uid: list(groups) for uid, groups in self.group_memberships.items()}

        # Build summary
        effective_count = sum(1 for perms in self.user_permissions.values()
                              for p in perms if p['effective_permission'] in ('Allow', 'InheritedAllow'))
        inherited_count = sum(1 for perms in self.user_permissions.values()
                              for p in perms if p['is_inherited'])

        summary = {
            'total_users': len(self.users),
            'total_groups': len(self.groups),
            'total_effective_permissions': effective_count,
            'total_inherited_permissions': inherited_count,
            'repositories': list(self.repository_permissions.keys())
        }

        # Categorize user permissions by type (direct, effective, etc.)
        categorized_user_permissions = {}
        for user_id, perms in self.user_permissions.items():
            categories = {
                'direct': [p for p in perms if not p['is_inherited']],
                'inherited': [p for p in perms if p['is_inherited']],
                'effective': [p for p in perms if p['effective_permission'] in ('Allow', 'InheritedAllow')]
            }
            categorized_user_permissions[user_id] = categories

        return {
            'groups': self.groups,
            'users': self.users,
            'group_memberships': group_memberships_list,
            'group_permissions': dict(self.group_permissions),
            'repository_permissions': dict(self.repository_permissions),
            'user_permissions': categorized_user_permissions,
            'summary': summary
        }
