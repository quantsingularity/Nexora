import React, { useState } from 'react';
import { 
  Box, 
  Grid, 
  Typography, 
  Card, 
  CardContent, 
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Alert,
  Snackbar,
  Paper,
  Tabs,
  Tab
} from '@mui/material';
import { 
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  CloudSync as CloudSyncIcon,
  Person as PersonIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import api from '../services/api';

const Settings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleSave = async () => {
    try {
      // In a real application, we would call an API to save settings
      // await api.saveSettings(settingsData);
      
      // For now, just simulate a successful save
      setSnackbarMessage('Settings saved successfully');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSnackbarMessage('Error saving settings. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  const handleHealthCheck = async () => {
    try {
      const result = await api.checkHealth();
      setSnackbarMessage(`System is ${result.status}. Last checked: ${new Date(result.timestamp).toLocaleString()}`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Health check failed:', error);
      setSnackbarMessage('System health check failed. Please contact support.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="settings tabs"
        >
          <Tab icon={<PersonIcon />} label="User Profile" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<NotificationsIcon />} label="Notifications" />
          <Tab icon={<StorageIcon />} label="Data Management" />
          <Tab icon={<SettingsIcon />} label="System" />
        </Tabs>
      </Paper>

      {/* User Profile Tab */}
      {activeTab === 0 && (
        <Card>
          <CardHeader title="User Profile" />
          <Divider />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  defaultValue="John"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  defaultValue="Doe"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  defaultValue="john.doe@hospital.org"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Phone"
                  defaultValue="(555) 123-4567"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Department"
                  defaultValue="Internal Medicine"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Role"
                  defaultValue="Attending Physician"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Make profile visible to other users"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Security Tab */}
      {activeTab === 1 && (
        <Card>
          <CardHeader title="Security Settings" />
          <Divider />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Current Password"
                  type="password"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="New Password"
                  type="password"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Confirm New Password"
                  type="password"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Two-Factor Authentication
                </Typography>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable two-factor authentication"
                />
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Session Settings
                </Typography>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Automatically log out after inactivity"
                />
                <TextField
                  fullWidth
                  label="Inactivity Timeout (minutes)"
                  type="number"
                  defaultValue={30}
                  margin="normal"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Notifications Tab */}
      {activeTab === 2 && (
        <Card>
          <CardHeader title="Notification Preferences" />
          <Divider />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="High-Risk Patient Alerts" 
                  secondary="Receive notifications when patients are identified as high-risk" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Model Update Notifications" 
                  secondary="Receive notifications when prediction models are updated" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="System Maintenance Alerts" 
                  secondary="Receive notifications about scheduled maintenance" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Weekly Summary Reports" 
                  secondary="Receive weekly summary of patient risk profiles" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Email Notifications" 
                  secondary="Receive notifications via email" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Mobile Push Notifications" 
                  secondary="Receive notifications on your mobile device" 
                />
                <Switch defaultChecked />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      )}

      {/* Data Management Tab */}
      {activeTab === 3 && (
        <Card>
          <CardHeader title="Data Management" />
          <Divider />
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Sources
            </Typography>
            <List>
              <ListItem>
                <ListItemIcon>
                  <StorageIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Electronic Health Record (EHR)" 
                  secondary="Connected: Epic Systems" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <StorageIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Laboratory Information System" 
                  secondary="Connected: Sunquest" 
                />
                <Switch defaultChecked />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <StorageIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Pharmacy System" 
                  secondary="Connected: Cerner PharmNet" 
                />
                <Switch defaultChecked />
              </ListItem>
            </List>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              Data Synchronization
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable automatic data synchronization"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Sync Frequency (hours)"
                  type="number"
                  defaultValue={4}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 3 }}>
                  <Button variant="outlined" startIcon={<CloudSyncIcon />}>
                    Sync Now
                  </Button>
                </Box>
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              Data Retention
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Patient Data Retention Period (years)"
                  type="number"
                  defaultValue={7}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Audit Log Retention Period (years)"
                  type="number"
                  defaultValue={10}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Automatically archive inactive patient records"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* System Tab */}
      {activeTab === 4 && (
        <Card>
          <CardHeader 
            title="System Settings" 
            action={
              <Button 
                variant="outlined" 
                size="small" 
                onClick={handleHealthCheck}
              >
                Check Health
              </Button>
            }
          />
          <Divider />
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Information
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="Application Version" 
                  secondary="Nexora v1.2.0" 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="Last Updated" 
                  secondary="April 10, 2025" 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="Database Status" 
                  secondary="Connected (MongoDB v5.0)" 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="API Status" 
                  secondary="Operational (v1.1)" 
                />
              </ListItem>
            </List>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              Performance Settings
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable caching for faster performance"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Preload patient data for assigned patients"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Maximum patients to preload"
                  type="number"
                  defaultValue={50}
                  margin="normal"
                />
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              Logging
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable detailed application logging"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Log all user actions for audit purposes"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  select
                  fullWidth
                  label="Log Level"
                  defaultValue="info"
                  margin="normal"
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </TextField>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button 
          variant="contained" 
          startIcon={<SaveIcon />}
          onClick={handleSave}
        >
          Save Settings
        </Button>
      </Box>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
