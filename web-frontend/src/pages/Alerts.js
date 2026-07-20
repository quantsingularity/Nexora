import {
  CheckCircleOutline as CheckCircleOutlineIcon,
  DoneAll as DoneAllIcon,
  ErrorOutline as ErrorOutlineIcon,
  InfoOutlined as InfoOutlinedIcon,
  Refresh as RefreshIcon,
  WarningAmberOutlined as WarningAmberOutlinedIcon,
} from "@mui/icons-material";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const SEVERITY_META = {
  critical: { color: "error", icon: <ErrorOutlineIcon />, label: "Critical" },
  warning: {
    color: "warning",
    icon: <WarningAmberOutlinedIcon />,
    label: "Warning",
  },
  info: { color: "info", icon: <InfoOutlinedIcon />, label: "Info" },
};

const timeAgo = (iso) => {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 60) return `${Math.max(mins, 0)}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
};

const Alerts = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notifications, setNotifications] = useState([]);

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getNotifications();
      setNotifications(data.notifications || []);
    } catch (err) {
      setError(err.message || "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkRead = async (id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
    try {
      await api.markNotificationRead(id);
    } catch (err) {
      // Revert on failure
      fetchNotifications();
    }
  };

  const handleMarkAllRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      await api.markAllNotificationsRead();
    } catch (err) {
      fetchNotifications();
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <Box>
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
            Alerts
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {loading
              ? "Loading…"
              : `${unreadCount} unread of ${notifications.length} alert${notifications.length !== 1 ? "s" : ""}`}
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchNotifications}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<DoneAllIcon />}
            onClick={handleMarkAllRead}
            disabled={loading || unreadCount === 0}
          >
            Mark all as read
          </Button>
        </Box>
      </Box>

      {loading && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
        </Box>
      )}

      {!loading && error && (
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={fetchNotifications}>
              Retry
            </Button>
          }
          sx={{ mb: 3 }}
        >
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <Card>
          {notifications.length === 0 ? (
            <CardContent sx={{ py: 6, textAlign: "center" }}>
              <CheckCircleOutlineIcon
                sx={{ fontSize: 48, color: "success.main", mb: 1 }}
              />
              <Typography color="text.secondary">
                All caught up. No alerts right now.
              </Typography>
            </CardContent>
          ) : (
            <List disablePadding>
              {notifications.map((n, i) => {
                const meta = SEVERITY_META[n.severity] || SEVERITY_META.info;
                return (
                  <Box key={n.id}>
                    <ListItem
                      alignItems="flex-start"
                      sx={{
                        py: 2,
                        px: 3,
                        bgcolor: n.read
                          ? "transparent"
                          : "rgba(37,99,235,0.04)",
                        cursor: n.patient_id ? "pointer" : "default",
                      }}
                      onClick={() => {
                        if (!n.read) handleMarkRead(n.id);
                        if (n.patient_id) navigate(`/patients/${n.patient_id}`);
                      }}
                      secondaryAction={
                        !n.read && (
                          <Button
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMarkRead(n.id);
                            }}
                          >
                            Mark read
                          </Button>
                        )
                      }
                    >
                      <ListItemAvatar>
                        <Avatar
                          sx={{
                            bgcolor: `${meta.color}.light`,
                            color: `${meta.color}.dark`,
                          }}
                        >
                          {meta.icon}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Typography sx={{ fontWeight: n.read ? 500 : 700 }}>
                              {n.title}
                            </Typography>
                            <Chip
                              label={meta.label}
                              color={meta.color}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={
                          <>
                            <Typography
                              component="span"
                              variant="body2"
                              color="text.secondary"
                              sx={{ display: "block", mt: 0.5 }}
                            >
                              {n.message}
                            </Typography>
                            <Typography
                              component="span"
                              variant="caption"
                              color="text.disabled"
                            >
                              {timeAgo(n.created_at)}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                    {i < notifications.length - 1 && <Divider component="li" />}
                  </Box>
                );
              })}
            </List>
          )}
        </Card>
      )}
    </Box>
  );
};

export default Alerts;
