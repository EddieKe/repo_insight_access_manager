/**
 * RepoInsightDashboard.jsx
 * Main dashboard component for RepoInsight Access Manager.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Box,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Badge,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  useMediaQuery,
  Drawer,
  Snackbar
} from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme, useTheme } from '@mui/material/styles';
import {
  Folder as FolderIcon,
  Group as GroupIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
  Storage as RepositoryIcon,
  AdminPanelSettings as AdminIcon,
  Visibility as VisibilityIcon,
  ExpandMore as ExpandMoreIcon,
  Close as CloseIcon,
  Settings as SettingsIcon,
  AccountCircle as AccountCircleIcon,
  Key as KeyIcon,
  Dashboard as DashboardIcon,
  Code as CodeIcon,
  LockOpen as LockOpenIcon,
  Menu as MenuIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Link as LinkIcon,
  History as HistoryIcon,
  Save as SaveIcon,
  FileDownload as FileDownloadIcon
} from '@mui/icons-material';

import * as RepoAPI from '../api/repoApi';

const DEFAULT_API_BASE = 'http://localhost:5000/v1';

// ----------------------------------------------------------------------
// Theme definition – deep purple primary, teal secondary
// ----------------------------------------------------------------------
const getAppTheme = (mode) => createTheme({
  palette: {
    mode,
    primary: {
      main: '#673ab7', // deep purple
      light: '#9a67ea',
      dark: '#320b86',
    },
    secondary: {
      main: '#009688', // teal
      light: '#52c7b8',
      dark: '#00675b',
    },
    background: {
      default: mode === 'dark' ? '#121212' : '#f5f5f7',
      paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  shape: {
    borderRadius: 8,
  },
});

// ----------------------------------------------------------------------
// TabPanel component
// ----------------------------------------------------------------------
function TabPanel({ children, value, index, ...other }) {
  return (
    <div role="tabpanel" hidden={value !== index} id={`tabpanel-${index}`} aria-labelledby={`tab-${index}`} {...other}>
      {value === index && <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>{children}</Box>}
    </div>
  );
}

// ----------------------------------------------------------------------
// Main component
// ----------------------------------------------------------------------
function RepoInsightDashboard() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));

  const [darkMode, setDarkMode] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [apiConfig, setApiConfig] = useState({ baseUrl: DEFAULT_API_BASE, orgUrl: '', apiToken: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [selectedRepo, setSelectedRepo] = useState('');
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [permissionsDialog, setPermissionsDialog] = useState(false);
  const [userPermissions, setUserPermissions] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [workspaces, setWorkspaces] = useState([]);
  const [repos, setRepos] = useState([]);
  const [teams, setTeams] = useState([]);
  const [teamMembers, setTeamMembers] = useState({});
  const [configurationComplete, setConfigurationComplete] = useState(false);
  const [configSaving, setConfigSaving] = useState(false);

  // ----------------------------------------------------------------------
  // Helper: headers for authenticated requests
  // ----------------------------------------------------------------------
  const getAuthHeaders = useCallback(() => {
    return {
      Authorization: `Basic ${btoa(`:${apiConfig.apiToken}`)}`,
      'X-Azure-DevOps-Organization-Url': apiConfig.orgUrl
    };
  }, [apiConfig.apiToken, apiConfig.orgUrl]);

  // ----------------------------------------------------------------------
  // Load workspaces (projects)
  // ----------------------------------------------------------------------
  const loadWorkspaces = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await RepoAPI.getWorkspaces(getAuthHeaders());
      const data = response.data;
      setWorkspaces(data);
      if (data.length > 0) {
        setSelectedWorkspace(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
      setError('Failed to load workspaces: ' + err.message);
      if (err.response?.status === 401 || err.message.includes('Authentication')) {
        setConfigDialogOpen(true);
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  // ----------------------------------------------------------------------
  // Load workspace data (repos + teams)
  // ----------------------------------------------------------------------
  const loadWorkspaceData = useCallback(async (workspaceId) => {
    try {
      setLoading(true);
      setError(null);
      const workspace = workspaces.find(w => w.id === workspaceId);
      if (!workspace) return;

      const reposRes = await RepoAPI.getRepos(workspace.name, getAuthHeaders());
      setRepos(reposRes.data);
      setSelectedRepo(reposRes.data.length > 0 ? reposRes.data[0].id : '');

      const teamsRes = await RepoAPI.getTeams(workspace.name, getAuthHeaders());
      setTeams(Object.values(teamsRes.data));
      setTeamMembers({});
    } catch (err) {
      console.error('Failed to load workspace data:', err);
      setError('Failed to load workspace data: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [workspaces, getAuthHeaders]);

  // ----------------------------------------------------------------------
  // Load repository members
  // ----------------------------------------------------------------------
  const loadRepoMembers = useCallback(async (repoId) => {
    if (!repoId) return;
    try {
      setLoading(true);
      const response = await RepoAPI.getRepoMembers(repoId, getAuthHeaders());
      setTeamMembers(prev => ({ ...prev, [repoId]: response.data }));
    } catch (err) {
      console.error('Failed to load repo members:', err);
      setError('Failed to load repo members: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  // ----------------------------------------------------------------------
  // Load team members (for a specific team descriptor)
  // ----------------------------------------------------------------------
  const loadTeamMembers = useCallback(async (descriptor) => {
    if (teamMembers[descriptor]) return;
    try {
      const response = await RepoAPI.getTeamMembers(descriptor, getAuthHeaders());
      setTeamMembers(prev => ({ ...prev, [descriptor]: response.data }));
    } catch (err) {
      console.error('Failed to load team members:', err);
      setNotification({ open: true, message: 'Failed to load team members: ' + err.message, severity: 'error' });
    }
  }, [teamMembers, getAuthHeaders]);

  // ----------------------------------------------------------------------
  // Load user rights (permissions) – global or per‑repo
  // ----------------------------------------------------------------------
  const loadUserRights = async (descriptor) => {
    try {
      setUserPermissions(null);
      let response;
      if (selectedRepo) {
        response = await RepoAPI.getUserRepoRights(selectedRepo, descriptor, getAuthHeaders());
      } else {
        response = await RepoAPI.getUserRights(descriptor, getAuthHeaders());
      }
      setUserPermissions(response.data);
      setPermissionsDialog(true);
    } catch (err) {
      console.error('Failed to load user rights:', err);
      setNotification({ open: true, message: 'Failed to load user rights: ' + err.message, severity: 'error' });
    }
  };

  // ----------------------------------------------------------------------
  // Export workspace report to Excel
  // ----------------------------------------------------------------------
  const handleExportWorkspace = async (workspaceId) => {
    try {
      setLoading(true);
      const workspace = workspaces.find(w => w.id === workspaceId);
      if (!workspace) throw new Error('Workspace not found');
      setNotification({ open: true, message: `Exporting ${workspace.name}...`, severity: 'info' });
      const response = await RepoAPI.exportWorkspaceReport(workspaceId, getAuthHeaders());
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${workspace.name}_access_report.xlsx`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      setNotification({ open: true, message: `Exported ${workspace.name} successfully`, severity: 'success' });
    } catch (err) {
      setNotification({ open: true, message: `Export failed: ${err.message}`, severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------------------------------------------------
  // Configuration (initial load from backend, fallback to localStorage)
  // ----------------------------------------------------------------------
  useEffect(() => {
    const storedOrgUrl = localStorage.getItem('orgUrl');
    const storedPat = localStorage.getItem('pat');
    if (storedOrgUrl && storedPat) {
      setApiConfig({
        baseUrl: localStorage.getItem('apiBaseUrl') || DEFAULT_API_BASE,
        orgUrl: storedOrgUrl,
        apiToken: storedPat
      });
      setConfigurationComplete(true);
    } else {
      RepoAPI.getConfig().then(res => {
        const cfg = res.data;
        if (cfg && cfg.org_url) {
          setApiConfig(prev => ({ ...prev, orgUrl: cfg.org_url }));
          if (cfg.api_token === '********') {
            setConfigurationComplete(true);
          } else {
            setConfigDialogOpen(true);
          }
        } else {
          setConfigDialogOpen(true);
        }
      }).catch(() => setConfigDialogOpen(true));
    }
  }, []);

  useEffect(() => {
    if (configurationComplete) loadWorkspaces();
  }, [configurationComplete, loadWorkspaces]);

  useEffect(() => {
    if (selectedWorkspace && configurationComplete) {
      loadWorkspaceData(selectedWorkspace);
    } else {
      setRepos([]);
      setTeams([]);
      setTeamMembers({});
    }
  }, [selectedWorkspace, configurationComplete, loadWorkspaceData]);

  useEffect(() => {
    if (selectedRepo && configurationComplete) {
      loadRepoMembers(selectedRepo);
    }
  }, [selectedRepo, configurationComplete, loadRepoMembers]);

  // ----------------------------------------------------------------------
  // Save configuration to backend and localStorage
  // ----------------------------------------------------------------------
  const saveConfiguration = async () => {
    try {
      setConfigSaving(true);
      localStorage.setItem('apiBaseUrl', apiConfig.baseUrl);
      localStorage.setItem('orgUrl', apiConfig.orgUrl);
      localStorage.setItem('pat', apiConfig.apiToken);
      await RepoAPI.saveConfig({ org_url: apiConfig.orgUrl, api_token: apiConfig.apiToken });
      setConfigurationComplete(true);
      setConfigDialogOpen(false);
      setNotification({ open: true, message: 'Configuration saved!', severity: 'success' });
      loadWorkspaces();
    } catch (err) {
      setNotification({ open: true, message: `Save failed: ${err.response?.data?.error || err.message}`, severity: 'error' });
    } finally {
      setConfigSaving(false);
    }
  };

  // ----------------------------------------------------------------------
  // Clear cache
  // ----------------------------------------------------------------------
  const handleClearCache = async () => {
    try {
      setRefreshing(true);
      await RepoAPI.clearCache();
      localStorage.removeItem('apiBaseUrl');
      localStorage.removeItem('orgUrl');
      localStorage.removeItem('pat');
      setRepos([]);
      setTeams([]);
      setTeamMembers({});
      setNotification({ open: true, message: 'Cache cleared. Data will refresh.', severity: 'success' });
      if (selectedWorkspace) loadWorkspaceData(selectedWorkspace);
      else loadWorkspaces();
    } catch (err) {
      setNotification({ open: true, message: `Clear cache failed: ${err.message}`, severity: 'error' });
    } finally {
      setRefreshing(false);
    }
  };

  const handleRefreshData = () => {
    if (selectedWorkspace) loadWorkspaceData(selectedWorkspace);
    else loadWorkspaces();
  };

  // ----------------------------------------------------------------------
  // UI helpers
  // ----------------------------------------------------------------------
  const getTeamTypeColor = (type) => {
    if (type === 'admin_group') return 'error';
    if (type === 'contributor_group') return 'primary';
    if (type === 'reader_group') return 'info';
    return 'default';
  };

  const getTeamTypeIcon = (type) => {
    if (type === 'admin_group') return <AdminIcon />;
    if (type === 'contributor_group') return <GroupIcon />;
    if (type === 'reader_group') return <VisibilityIcon />;
    return <SecurityIcon />;
  };

  const currentWorkspace = workspaces.find(w => w.id === selectedWorkspace);
  const currentRepo = repos.find(r => r.id === selectedRepo);
  const filteredTeams = teams.filter(t =>
    !userSearchQuery ||
    (t.display_name?.toLowerCase().includes(userSearchQuery.toLowerCase())) ||
    (t.account_name?.toLowerCase().includes(userSearchQuery.toLowerCase()))
  );

  if (loading && !configDialogOpen) {
    return (
      <ThemeProvider theme={getAppTheme(darkMode ? 'dark' : 'light')}>
        <CssBaseline />
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" flexDirection="column">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>Loading platform data...</Typography>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={getAppTheme(darkMode ? 'dark' : 'light')}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {/* App Bar */}
        <AppBar position="static" color="primary" elevation={4}>
          <Toolbar>
            {isMobile && (
              <IconButton edge="start" color="inherit" onClick={() => setDrawerOpen(true)} sx={{ mr: 2 }}>
                <MenuIcon />
              </IconButton>
            )}
            <DashboardIcon sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
              RepoInsight Access Manager
            </Typography>
            {!isMobile && currentWorkspace && (
              <Chip label={currentWorkspace.name} variant="outlined" sx={{ color: 'white', borderColor: 'white', mr: 2 }} />
            )}
            {!isMobile && currentRepo && (
              <Chip label={currentRepo.name} variant="outlined" sx={{ color: 'white', borderColor: 'white', mr: 2 }} />
            )}
            <Tooltip title="Refresh">
              <IconButton color="inherit" onClick={handleRefreshData} disabled={refreshing}>
                {refreshing ? <CircularProgress color="inherit" size={24} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Clear Cache">
              <IconButton color="inherit" onClick={handleClearCache}>
                <HistoryIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Settings">
              <IconButton color="inherit" onClick={() => setConfigDialogOpen(true)}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={darkMode ? 'Light Mode' : 'Dark Mode'}>
              <IconButton color="inherit" onClick={() => setDarkMode(!darkMode)}>
                {darkMode ? <LockOpenIcon /> : <SecurityIcon />}
              </IconButton>
            </Tooltip>
          </Toolbar>
        </AppBar>

        {/* Mobile drawer */}
        <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
          <Box sx={{ width: 250, p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Navigation</Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              <ListItem button onClick={() => { setTabValue(0); setDrawerOpen(false); }}>
                <ListItemIcon><FolderIcon color={tabValue === 0 ? 'primary' : 'inherit'} /></ListItemIcon>
                <ListItemText primary="Workspaces" />
              </ListItem>
              <ListItem button onClick={() => { setTabValue(1); setDrawerOpen(false); }}>
                <ListItemIcon><RepositoryIcon color={tabValue === 1 ? 'primary' : 'inherit'} /></ListItemIcon>
                <ListItemText primary="Code Repos" />
              </ListItem>
              <ListItem button onClick={() => { setTabValue(2); setDrawerOpen(false); }}>
                <ListItemIcon><GroupIcon color={tabValue === 2 ? 'primary' : 'inherit'} /></ListItemIcon>
                <ListItemText primary="Teams & Access" />
              </ListItem>
              <ListItem button onClick={() => { setTabValue(3); setDrawerOpen(false); }}>
                <ListItemIcon><PersonIcon color={tabValue === 3 ? 'primary' : 'inherit'} /></ListItemIcon>
                <ListItemText primary="Repo Members" />
              </ListItem>
            </List>
            <Divider sx={{ my: 2 }} />
            <FormControlLabel control={<Switch checked={darkMode} onChange={() => setDarkMode(!darkMode)} />} label="Dark Mode" />
          </Box>
        </Drawer>

        {/* Main content */}
        <Container disableGutters maxWidth={false} sx={{ mt: 3, flexGrow: 1, width: '100vw', px: 3 }}>
          {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}

          {/* Workspace & Repo selectors */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>Workspace</InputLabel>
                <Select value={selectedWorkspace} label="Workspace" onChange={(e) => setSelectedWorkspace(e.target.value)} disabled={workspaces.length === 0}>
                  {workspaces.map(ws => <MenuItem key={ws.id} value={ws.id}>{ws.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined" disabled={repos.length === 0}>
                <InputLabel>Repository</InputLabel>
                <Select value={selectedRepo} label="Repository" onChange={(e) => setSelectedRepo(e.target.value)}>
                  {repos.map(repo => <MenuItem key={repo.id} value={repo.id}>{repo.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} variant={isMedium ? "scrollable" : "standard"} scrollButtons={isMedium ? "auto" : false}>
              <Tab label="Workspaces" icon={<FolderIcon />} iconPosition="start" />
              <Tab label="Code Repos" icon={<RepositoryIcon />} iconPosition="start" />
              <Tab label="Teams & Access" icon={<GroupIcon />} iconPosition="start" />
              <Tab label="Repo Members" icon={<PersonIcon />} iconPosition="start" />
            </Tabs>
          </Box>

          {/* Tab 0: Workspaces */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              {workspaces.map(ws => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={ws.id}>
                  <Card elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column', border: ws.id === selectedWorkspace ? `2px solid ${theme.palette.primary.main}` : 'none' }}>
                    <CardHeader avatar={<Avatar sx={{ bgcolor: theme.palette.primary.main }}><FolderIcon /></Avatar>} title={ws.name} titleTypographyProps={{ variant: 'h6' }} subheader={<><Chip label={ws.state} color={ws.state === 'wellFormed' ? 'success' : 'default'} size="small" sx={{ mr: 1 }} /><Chip label={ws.visibility} size="small" /></>} />
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="text.secondary">{ws.description || 'No description'}</Typography>
                    </CardContent>
                    <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                      <Button size="small" variant="outlined" onClick={() => setSelectedWorkspace(ws.id)}>Select</Button>
                      <Button size="small" variant="contained" color="primary" onClick={() => { setSelectedWorkspace(ws.id); setTabValue(1); }}>View Repos</Button>
                      <Tooltip title="Export to Excel"><IconButton onClick={() => handleExportWorkspace(ws.id)}><FileDownloadIcon /></IconButton></Tooltip>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>

          {/* Tab 1: Repositories */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              {repos.map(repo => (
                <Grid item xs={12} sm={6} md={4} key={repo.id}>
                  <Card elevation={3} sx={{ height: '100%', border: repo.id === selectedRepo ? `2px solid ${theme.palette.primary.main}` : 'none' }}>
                    <CardHeader avatar={<Avatar sx={{ bgcolor: theme.palette.secondary.main }}><RepositoryIcon /></Avatar>} title={repo.name} subheader={`Default branch: ${repo.defaultBranch?.replace('refs/heads/', '') || 'main'}`} />
                    <CardContent><Typography variant="body2">ID: {repo.id}</Typography></CardContent>
                    <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                      <Button size="small" variant="outlined" onClick={() => setSelectedRepo(repo.id)}>Select</Button>
                      <Button size="small" variant="contained" color="primary" onClick={() => { setSelectedRepo(repo.id); setTabValue(2); }}>Access Rights</Button>
                      <Tooltip title="Open in Platform"><IconButton href={repo.url} target="_blank"><LinkIcon /></IconButton></Tooltip>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>

          {/* Tab 2: Teams & Access */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4} lg={3}>
                <Card elevation={3} sx={{ mb: 3 }}>
                  <CardHeader title="Filter Teams" />
                  <CardContent>
                    <TextField fullWidth variant="outlined" label="Search teams" value={userSearchQuery} onChange={e => setUserSearchQuery(e.target.value)} InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} /> }} sx={{ mb: 2 }} />
                    <Typography variant="body2">Showing {filteredTeams.length} of {teams.length}</Typography>
                  </CardContent>
                </Card>
                <Card elevation={3}>
                  <CardHeader title="Repository Info" />
                  <CardContent>
                    {currentRepo ? (
                      <>
                        <Typography variant="subtitle1">{currentRepo.name}</Typography>
                        <Button fullWidth variant="outlined" startIcon={<LinkIcon />} href={currentRepo.url} target="_blank" sx={{ mt: 1 }}>Open in Platform</Button>
                      </>
                    ) : <Typography variant="body2">Select a repository to see details</Typography>}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={8} lg={9}>
                <Card elevation={3}>
                  <CardContent>
                    <Typography variant="h5" gutterBottom><GroupIcon sx={{ mr: 1, verticalAlign: 'middle' }} /> Teams & Members</Typography>
                    {filteredTeams.map(team => (
                      <Accordion key={team.id} sx={{ mb: 2 }} onChange={(e, expanded) => { if (expanded) loadTeamMembers(team.descriptor); }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box display="flex" alignItems="center" width="100%">
                            {getTeamTypeIcon(team.group_type)}
                            <Typography variant="subtitle1" sx={{ ml: 1, flexGrow: 1 }}>{team.display_name || team.account_name}</Typography>
                            <Chip label={team.group_type?.replace('_', ' ') || 'team'} color={getTeamTypeColor(team.group_type)} size="small" sx={{ mr: 1 }} />
                            {teamMembers[team.descriptor] && <Badge badgeContent={teamMembers[team.descriptor].length} color="primary"><PersonIcon /></Badge>}
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          {!teamMembers[team.descriptor] ? <Box display="flex" justifyContent="center" py={2}><CircularProgress size={24} /></Box> : teamMembers[team.descriptor].length === 0 ? <Typography variant="body2">No members</Typography> : (
                            <TableContainer component={Paper} variant="outlined">
                              <Table size="small">
                                <TableHead><TableRow><TableCell>Name</TableCell><TableCell>Email</TableCell><TableCell>Origin</TableCell><TableCell align="right">Actions</TableCell></TableRow></TableHead>
                                <TableBody>
                                  {teamMembers[team.descriptor].map(member => (
                                    <TableRow key={member.descriptor}>
                                      <TableCell><Box display="flex" alignItems="center"><Avatar sx={{ width: 24, height: 24, mr: 1, bgcolor: theme.palette.primary.main }}>{member.display_name?.charAt(0) || '?'}</Avatar>{member.display_name}</Box></TableCell>
                                      <TableCell>{member.mail_address || 'N/A'}</TableCell>
                                      <TableCell>{member.origin}</TableCell>
                                      <TableCell align="right"><Tooltip title="View Rights"><IconButton size="small" onClick={() => loadUserRights(member.descriptor)}><SecurityIcon /></IconButton></Tooltip></TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </TableContainer>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 3: Repository Members */}
          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4} lg={3}>
                <Card elevation={3} sx={{ mb: 3 }}>
                  <CardHeader title="Filter Members" />
                  <CardContent>
                    <TextField fullWidth variant="outlined" label="Search" value={userSearchQuery} onChange={e => setUserSearchQuery(e.target.value)} InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1 }} /> }} sx={{ mb: 2 }} />
                    {teamMembers[selectedRepo] && <Typography variant="body2">{teamMembers[selectedRepo].length} members</Typography>}
                  </CardContent>
                </Card>
                <Card elevation={3}>
                  <CardHeader title="Repository Info" />
                  <CardContent>
                    {currentRepo ? (
                      <>
                        <Typography variant="subtitle1">{currentRepo.name}</Typography>
                        <Button fullWidth variant="outlined" startIcon={<LinkIcon />} href={currentRepo.url} target="_blank" sx={{ mt: 1 }}>Open in Platform</Button>
                      </>
                    ) : <Typography variant="body2">Select a repository</Typography>}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={8} lg={9}>
                <Card elevation={3}>
                  <CardHeader title="Direct Repository Members" action={<Tooltip title="Refresh"><IconButton onClick={() => loadRepoMembers(selectedRepo)}><RefreshIcon /></IconButton></Tooltip>} />
                  <CardContent>
                    {!currentRepo ? <Alert severity="info">Select a repository</Alert> : loading ? <Box display="flex" justifyContent="center" py={4}><CircularProgress /></Box> : (
                      <TableContainer component={Paper} variant="outlined">
                        <Table>
                          <TableHead><TableRow><TableCell>Name</TableCell><TableCell>Email</TableCell><TableCell>Role</TableCell><TableCell>Origin</TableCell><TableCell align="right">Actions</TableCell></TableRow></TableHead>
                          <TableBody>
                            {(teamMembers[selectedRepo] || []).filter(m => !userSearchQuery || (m.display_name?.toLowerCase().includes(userSearchQuery.toLowerCase()) || m.mail_address?.toLowerCase().includes(userSearchQuery.toLowerCase()))).map(m => (
                              <TableRow key={m.descriptor}>
                                <TableCell><Box display="flex" alignItems="center"><Avatar sx={{ width: 24, height: 24, mr: 1, bgcolor: m.role === 'Admin' ? theme.palette.error.main : theme.palette.primary.main }}>{m.display_name?.charAt(0) || '?'}</Avatar>{m.display_name}</Box></TableCell>
                                <TableCell>{m.mail_address || 'N/A'}</TableCell>
                                <TableCell><Chip label={m.role} size="small" color={m.role === 'Admin' ? 'error' : 'primary'} /></TableCell>
                                <TableCell>{m.origin}</TableCell>
                                <TableCell align="right"><Tooltip title="View Rights"><IconButton size="small" onClick={() => loadUserRights(m.descriptor)}><SecurityIcon /></IconButton></Tooltip></TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </Container>

        {/* Footer */}
        <Box component="footer" sx={{ py: 2, px: 2, mt: 'auto', bgcolor: theme.palette.mode === 'dark' ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.05)', borderTop: `1px solid ${theme.palette.divider}` }}>
          <Typography variant="body2" color="text.secondary" align="center">RepoInsight Access Manager | {new Date().getFullYear()}</Typography>
        </Box>

        {/* Configuration Dialog */}
        <Dialog open={configDialogOpen} onClose={() => configurationComplete && setConfigDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Platform Connection Settings{configurationComplete && <IconButton onClick={() => setConfigDialogOpen(false)} sx={{ position: 'absolute', right: 8, top: 8 }}><CloseIcon /></IconButton>}</DialogTitle>
          <DialogContent>
            <Box sx={{ my: 2 }}>
              <Alert severity="info" sx={{ mb: 3 }}>Provide your organization URL and personal access token (PAT).</Alert>
              <TextField label="API Base URL" fullWidth variant="outlined" margin="normal" value={apiConfig.baseUrl} onChange={e => setApiConfig({...apiConfig, baseUrl: e.target.value})} placeholder="http://localhost:5000/v1" InputProps={{ startAdornment: <LinkIcon sx={{ mr: 1 }} /> }} />
              <TextField label="Organization URL" fullWidth variant="outlined" margin="normal" value={apiConfig.orgUrl} onChange={e => setApiConfig({...apiConfig, orgUrl: e.target.value})} placeholder="https://dev.azure.com/your-org" required InputProps={{ startAdornment: <LinkIcon sx={{ mr: 1 }} /> }} />
              <TextField label="Personal Access Token" fullWidth variant="outlined" margin="normal" value={apiConfig.apiToken} onChange={e => setApiConfig({...apiConfig, apiToken: e.target.value})} placeholder="Your PAT" type="password" required InputProps={{ startAdornment: <KeyIcon sx={{ mr: 1 }} /> }} helperText="If already saved, leave empty to keep current token." />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={saveConfiguration} variant="contained" color="primary" disabled={!apiConfig.orgUrl || (configurationComplete ? false : !apiConfig.apiToken) || configSaving} startIcon={configSaving ? <CircularProgress size={16} /> : <SaveIcon />}>{configSaving ? 'Saving...' : 'Save Configuration'}</Button>
          </DialogActions>
        </Dialog>

        {/* Permissions Dialog */}
        <Dialog open={permissionsDialog} onClose={() => setPermissionsDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>User Access Rights<IconButton onClick={() => setPermissionsDialog(false)} sx={{ position: 'absolute', right: 8, top: 8 }}><CloseIcon /></IconButton></DialogTitle>
          <DialogContent>
            {!userPermissions ? <Box display="flex" justifyContent="center" py={4}><CircularProgress /></Box> : (
              <Box>
                {userPermissions.user && <><Typography variant="h6">{userPermissions.user.displayName}</Typography><Typography variant="body2" color="text.secondary">User ID: {userPermissions.user.id}</Typography></>}
                {userPermissions.repository && <><Typography variant="h6" sx={{ mt: 2 }}>Repository: {userPermissions.repository.name}</Typography><Typography variant="body2">ID: {userPermissions.repository.id}</Typography></>}
                {userPermissions.permissions ? Object.entries(userPermissions.permissions).map(([cat, perms]) => (
                  <Accordion key={cat} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>{cat} ({perms.length})</Typography></AccordionSummary>
                    <AccordionDetails>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small"><TableHead><TableRow><TableCell>Permission</TableCell><TableCell>Status</TableCell><TableCell>Inherited</TableCell></TableRow></TableHead>
                        <TableBody>{perms.map((p, i) => <TableRow key={i}><TableCell>{p.permission_name}</TableCell><TableCell><Chip label={p.effective_permission} color={p.effective_permission.includes('Allow') ? 'success' : p.effective_permission === 'NotSet' ? 'default' : 'error'} size="small" /></TableCell><TableCell>{p.is_inherited ? 'Yes' : 'No'}</TableCell></TableRow>)}</TableBody></Table>
                      </TableContainer>
                    </AccordionDetails>
                  </Accordion>
                )) : <Alert severity="info">No permissions found.</Alert>}
              </Box>
            )}
          </DialogContent>
          <DialogActions><Button onClick={() => setPermissionsDialog(false)} variant="outlined">Close</Button></DialogActions>
        </Dialog>

        <Snackbar open={notification.open} autoHideDuration={6000} onClose={() => setNotification({...notification, open: false})} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
          <Alert onClose={() => setNotification({...notification, open: false})} severity={notification.severity} sx={{ width: '100%' }}>{notification.message}</Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

export default RepoInsightDashboard;
