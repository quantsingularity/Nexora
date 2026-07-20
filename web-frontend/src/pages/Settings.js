import {
  CheckCircle as CheckCircleIcon,
  ErrorOutline as ErrorOutlineIcon,
  Person as PersonIcon,
  Save as SaveIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
  Snackbar,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

const Settings = () => {
  const { user, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  // ── Profile form ──────────────────────────────────────────────────────
  const [profileForm, setProfileForm] = useState({
    fullName: "",
    organization: "",
    specialty: "",
  });
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileForm({
        fullName: user.full_name || "",
        organization: user.organization || "",
        specialty: user.specialty || "",
      });
    }
  }, [user]);

  const showSnackbar = (message, severity = "success") =>
    setSnackbar({ open: true, message, severity });

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      await api.updateProfile(profileForm);
      await refreshUser();
      showSnackbar("Profile updated successfully.");
    } catch (err) {
      showSnackbar(err.message || "Failed to update profile.", "error");
    } finally {
      setSavingProfile(false);
    }
  };

  // ── Security form ─────────────────────────────────────────────────────
  const [pwForm, setPwForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [savingPassword, setSavingPassword] = useState(false);

  const handleChangePassword = async () => {
    if (pwForm.newPassword !== pwForm.confirmPassword) {
      showSnackbar("New passwords do not match.", "error");
      return;
    }
    if (pwForm.newPassword.length < 8) {
      showSnackbar("New password must be at least 8 characters.", "error");
      return;
    }
    setSavingPassword(true);
    try {
      await api.changePassword({
        currentPassword: pwForm.currentPassword,
        newPassword: pwForm.newPassword,
      });
      setPwForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      showSnackbar("Password changed successfully.");
    } catch (err) {
      showSnackbar(err.message || "Failed to change password.", "error");
    } finally {
      setSavingPassword(false);
    }
  };

  // ── System tab ────────────────────────────────────────────────────────
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState(null);
  const [checkingHealth, setCheckingHealth] = useState(false);

  const handleHealthCheck = async () => {
    setCheckingHealth(true);
    setHealthError(null);
    try {
      const result = await api.checkHealth();
      setHealth(result);
    } catch (err) {
      setHealthError(err.message || "System health check failed.");
      setHealth(null);
    } finally {
      setCheckingHealth(false);
    }
  };

  useEffect(() => {
    handleHealthCheck();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Manage your account, security, and system status
        </Typography>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_e, v) => setActiveTab(v)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<PersonIcon />} iconPosition="start" label="Profile" />
          <Tab icon={<SecurityIcon />} iconPosition="start" label="Security" />
          <Tab icon={<SettingsIcon />} iconPosition="start" label="System" />
        </Tabs>
      </Paper>

      {/* Profile Tab */}
      {activeTab === 0 && (
        <Card>
          <CardHeader title="User Profile" />
          <Divider />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Full Name"
                  value={profileForm.fullName}
                  onChange={(e) =>
                    setProfileForm((f) => ({ ...f, fullName: e.target.value }))
                  }
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  value={user?.email || ""}
                  margin="normal"
                  disabled
                  helperText="Email cannot be changed"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Organization"
                  value={profileForm.organization}
                  onChange={(e) =>
                    setProfileForm((f) => ({
                      ...f,
                      organization: e.target.value,
                    }))
                  }
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Specialty"
                  value={profileForm.specialty}
                  onChange={(e) =>
                    setProfileForm((f) => ({ ...f, specialty: e.target.value }))
                  }
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Account created{" "}
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString()
                    : "N/A"}
                  {user?.last_login_at &&
                    ` · Last sign-in ${new Date(user.last_login_at).toLocaleString()}`}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
          <Divider />
          <Box sx={{ p: 2, display: "flex", justifyContent: "flex-end" }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveProfile}
              disabled={savingProfile}
            >
              {savingProfile ? "Saving…" : "Save Profile"}
            </Button>
          </Box>
        </Card>
      )}

      {/* Security Tab */}
      {activeTab === 1 && (
        <Card>
          <CardHeader title="Change Password" />
          <Divider />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Current Password"
                  type="password"
                  margin="normal"
                  value={pwForm.currentPassword}
                  onChange={(e) =>
                    setPwForm((f) => ({
                      ...f,
                      currentPassword: e.target.value,
                    }))
                  }
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="New Password"
                  type="password"
                  margin="normal"
                  value={pwForm.newPassword}
                  onChange={(e) =>
                    setPwForm((f) => ({ ...f, newPassword: e.target.value }))
                  }
                  helperText="At least 8 characters, with a letter and a number"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Confirm New Password"
                  type="password"
                  margin="normal"
                  value={pwForm.confirmPassword}
                  onChange={(e) =>
                    setPwForm((f) => ({
                      ...f,
                      confirmPassword: e.target.value,
                    }))
                  }
                />
              </Grid>
            </Grid>
          </CardContent>
          <Divider />
          <Box sx={{ p: 2, display: "flex", justifyContent: "flex-end" }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleChangePassword}
              disabled={
                savingPassword || !pwForm.currentPassword || !pwForm.newPassword
              }
            >
              {savingPassword ? "Updating…" : "Update Password"}
            </Button>
          </Box>
        </Card>
      )}

      {/* System Tab */}
      {activeTab === 2 && (
        <Card>
          <CardHeader
            title="System Status"
            action={
              <Button
                variant="outlined"
                size="small"
                onClick={handleHealthCheck}
                disabled={checkingHealth}
              >
                {checkingHealth ? "Checking…" : "Check Health"}
              </Button>
            }
          />
          <Divider />
          <CardContent>
            {health && (
              <Alert
                icon={<CheckCircleIcon />}
                severity="success"
                sx={{ mb: 3 }}
              >
                Backend is {health.status} (v{health.version}), last checked{" "}
                {new Date(health.timestamp).toLocaleString()}
              </Alert>
            )}
            {healthError && (
              <Alert
                icon={<ErrorOutlineIcon />}
                severity="error"
                sx={{ mb: 3 }}
              >
                {healthError}
              </Alert>
            )}

            <List>
              <ListItem divider>
                <ListItemText
                  primary="Application Version"
                  secondary="Nexora v1.3.0"
                />
              </ListItem>
              <ListItem divider>
                <ListItemText
                  primary="API Base URL"
                  secondary={
                    process.env.REACT_APP_API_BASE_URL ||
                    "http://localhost:8000"
                  }
                />
              </ListItem>
              <ListItem divider>
                <ListItemText
                  primary="Signed in as"
                  secondary={user ? `${user.full_name} (${user.role})` : "N/A"}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Compliance"
                  secondary="All patient record access is written to the HIPAA audit log."
                />
                <Chip
                  label="HIPAA-aware"
                  color="primary"
                  size="small"
                  variant="outlined"
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          severity={snackbar.severity}
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
