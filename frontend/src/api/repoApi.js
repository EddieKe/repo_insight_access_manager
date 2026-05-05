/**
 * repoApi.js
 * API client for the RepoInsight Access Manager backend.
 */

import axios from 'axios';

const API_BASE = 'http://localhost:5000/v1';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: false,
});

// ----------------------------------------------------------------------
// Configuration
// ----------------------------------------------------------------------
export const getConfig = () => api.get('/config/platform');
export const saveConfig = (config) => api.post('/config/platform', config);
export const clearCache = () => api.post('/cache/clear');

// ----------------------------------------------------------------------
// Workspaces
// ----------------------------------------------------------------------
export const getWorkspaces = (headers) => api.get('/workspaces', { headers });
export const getWorkspaceDetail = (wsId, headers) => api.get(`/workspaces/${wsId}`, { headers });
export const getRepos = (wsId, headers) => api.get(`/workspaces/${wsId}/repos`, { headers });
export const getTeams = (wsId, headers) => api.get(`/workspaces/${wsId}/teams`, { headers });

// ----------------------------------------------------------------------
// Repositories
// ----------------------------------------------------------------------
export const getRepoAccess = (repoId, headers) => api.get(`/repos/${repoId}/access`, { headers });
export const getRepoMembers = (repoId, headers) => api.get(`/repos/${repoId}/members`, { headers });
export const getUserRepoRights = (repoId, descriptor, headers) =>
  api.get(`/repos/${repoId}/users/${descriptor}/rights`, { headers });

// ----------------------------------------------------------------------
// Teams & Users
// ----------------------------------------------------------------------
export const getTeamMembers = (descriptor, headers) => api.get(`/teams/${descriptor}/members`, { headers });
export const getUserRights = (descriptor, headers) => api.get(`/users/${descriptor}/rights`, { headers });

// ----------------------------------------------------------------------
// Export
// ----------------------------------------------------------------------
export const exportWorkspaceReport = (wsId, headers) =>
  api.get(`/workspaces/${wsId}/export-report`, { responseType: 'blob', headers });
