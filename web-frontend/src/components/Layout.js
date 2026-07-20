import {
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  Home as HomeIcon,
  Menu as MenuIcon,
  NotificationsActive as NotificationsActiveIcon,
  Notifications as NotificationsIcon,
  People as PeopleIcon,
  Science as ScienceIcon,
  Settings as SettingsIcon,
} from "@mui/icons-material";
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useEffect, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

const drawerWidth = 240;

const menuItems = [
  { text: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
  { text: "Patients", icon: <PeopleIcon />, path: "/patients" },
  { text: "Models", icon: <ScienceIcon />, path: "/models" },
  { text: "Alerts", icon: <NotificationsActiveIcon />, path: "/alerts" },
  { text: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

const getInitials = (name) =>
  (name || "")
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0].toUpperCase())
    .slice(0, 2)
    .join("");

function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(!isMobile);
  const [anchorEl, setAnchorEl] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [systemStatus, setSystemStatus] = useState("checking");

  const handleDrawerToggle = () => setOpen((prev) => !prev);
  const handleProfileMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleProfileMenuClose = () => setAnchorEl(null);

  useEffect(() => {
    let mounted = true;
    api
      .getNotifications()
      .then((data) => {
        if (mounted) setUnreadCount(data.unread || 0);
      })
      .catch(() => {
        if (mounted) setUnreadCount(0);
      });
    api
      .checkHealth()
      .then(() => mounted && setSystemStatus("healthy"))
      .catch(() => mounted && setSystemStatus("unreachable"));
    return () => {
      mounted = false;
    };
    // Refresh whenever the route changes so the badge stays current after
    // visiting the Alerts page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  const handleLogout = async () => {
    handleProfileMenuClose();
    await logout();
    navigate("/");
  };

  // Active check: supports nested routes like /patients/:id
  const isActive = (path) => {
    if (path === "/dashboard") return location.pathname === "/dashboard";
    return location.pathname.startsWith(path);
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
          background: "white",
          color: "primary.main",
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            {open && !isMobile ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>

          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              variant="h6"
              noWrap
              component={Link}
              to="/dashboard"
              sx={{ fontWeight: 800, textDecoration: "none", color: "inherit" }}
            >
              NEXORA
            </Typography>
            <Typography
              variant="caption"
              sx={{
                ml: 1,
                opacity: 0.55,
                display: { xs: "none", sm: "block" },
              }}
            >
              Clinical Prediction System
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <Tooltip title="Home">
              <IconButton color="inherit" component={Link} to="/">
                <HomeIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Notifications">
              <IconButton color="inherit" component={Link} to="/alerts">
                <Badge badgeContent={unreadCount} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Account">
              <IconButton
                edge="end"
                aria-label="account"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main" }}>
                  {getInitials(user?.full_name) || "?"}
                </Avatar>
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleProfileMenuClose}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
              PaperProps={{ elevation: 3, sx: { minWidth: 220, mt: 0.5 } }}
            >
              <MenuItem disabled sx={{ opacity: "1 !important" }}>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {user?.full_name || "Signed in"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user?.email}
                  </Typography>
                </Box>
              </MenuItem>
              <Divider />
              <MenuItem
                onClick={() => {
                  handleProfileMenuClose();
                  navigate("/settings");
                }}
              >
                Profile & Settings
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
                Sign Out
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isMobile ? "temporary" : "persistent"}
        open={open}
        onClose={isMobile ? handleDrawerToggle : undefined}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            background: theme.palette.background.default,
            borderRight: "1px solid rgba(0,0,0,0.08)",
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto", mt: 1 }}>
          <List>
            {menuItems.map((item) => {
              const active = isActive(item.path);
              return (
                <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    component={Link}
                    to={item.path}
                    selected={active}
                    sx={{
                      borderRadius: "0 24px 24px 0",
                      mx: 1,
                      backgroundColor: active
                        ? "rgba(37, 99, 235, 0.12)"
                        : "transparent",
                      "&:hover": {
                        backgroundColor: active
                          ? "rgba(37, 99, 235, 0.18)"
                          : "rgba(37, 99, 235, 0.06)",
                      },
                      "&.Mui-selected": {
                        backgroundColor: "rgba(37, 99, 235, 0.12)",
                      },
                      "&.Mui-selected:hover": {
                        backgroundColor: "rgba(37, 99, 235, 0.18)",
                      },
                    }}
                    onClick={isMobile ? handleDrawerToggle : undefined}
                  >
                    <ListItemIcon
                      sx={{
                        color: active ? "primary.main" : "text.secondary",
                        minWidth: 40,
                      }}
                    >
                      {item.text === "Alerts" && unreadCount > 0 ? (
                        <Badge badgeContent={unreadCount} color="error">
                          {item.icon}
                        </Badge>
                      ) : (
                        item.icon
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{
                        fontWeight: active ? 700 : 400,
                        color: active ? "primary.main" : "text.primary",
                        fontSize: "0.9rem",
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ px: 2 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mb: 1, display: "block" }}
            >
              System Status
            </Typography>
            <Box
              sx={{
                p: 1.5,
                bgcolor:
                  systemStatus === "healthy"
                    ? "success.light"
                    : systemStatus === "checking"
                      ? "grey.200"
                      : "error.light",
                color: systemStatus === "checking" ? "text.secondary" : "white",
                borderRadius: 2,
                fontSize: "0.8rem",
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  bgcolor:
                    systemStatus === "checking" ? "text.disabled" : "white",
                  flexShrink: 0,
                  "@keyframes pulse": {
                    "0%": { boxShadow: "0 0 0 0 rgba(255,255,255,0.6)" },
                    "70%": { boxShadow: "0 0 0 6px rgba(255,255,255,0)" },
                    "100%": { boxShadow: "0 0 0 0 rgba(255,255,255,0)" },
                  },
                  animation:
                    systemStatus === "healthy" ? "pulse 2s infinite" : "none",
                }}
              />
              {systemStatus === "healthy" && "All systems operational"}
              {systemStatus === "checking" && "Checking backend…"}
              {systemStatus === "unreachable" && "Backend unreachable"}
            </Box>
          </Box>

          <Box sx={{ px: 2, mt: 3 }}>
            <Typography variant="caption" color="text.disabled">
              Nexora v1.3.0
            </Typography>
          </Box>
        </Box>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          pt: 10,
          minHeight: "100vh",
          bgcolor: "background.default",
          width: "100%",
          transition: theme.transitions.create(["margin", "width"], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(open &&
            !isMobile && {
              marginLeft: 0,
              width: `calc(100% - ${drawerWidth}px)`,
              transition: theme.transitions.create(["margin", "width"], {
                easing: theme.transitions.easing.easeOut,
                duration: theme.transitions.duration.enteringScreen,
              }),
            }),
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}

export default Layout;
