import {
  LocalHospital as HospitalIcon,
  PersonAdd as PersonAddIcon,
  Visibility,
  VisibilityOff,
} from "@mui/icons-material";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  InputAdornment,
  Link as MuiLink,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { brand } from "../assets/styles/theme";
import { useAuth } from "../context/AuthContext";

const SignUp = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    organization: "",
    specialty: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    if (!form.fullName.trim() || !form.email.trim() || !form.password) {
      return "Please fill in your name, email, and password.";
    }
    if (form.password.length < 8) {
      return "Password must be at least 8 characters long.";
    }
    if (!/\d/.test(form.password) || !/[a-zA-Z]/.test(form.password)) {
      return "Password must contain at least one letter and one number.";
    }
    if (form.password !== form.confirmPassword) {
      return "Passwords do not match.";
    }
    return "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register({
        fullName: form.fullName.trim(),
        email: form.email.trim(),
        password: form.password,
        organization: form.organization.trim() || undefined,
        specialty: form.specialty.trim() || undefined,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(
        err.message || "Unable to create your account. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: brand.gradient,
        p: 2,
        py: 5,
      }}
    >
      <Card sx={{ maxWidth: 520, width: "100%", borderRadius: 4 }}>
        <CardContent sx={{ p: 5 }}>
          <Box sx={{ textAlign: "center", mb: 4 }}>
            <Avatar
              component={Link}
              to="/"
              sx={{
                bgcolor: "primary.main",
                width: 64,
                height: 64,
                mx: "auto",
                mb: 2,
                textDecoration: "none",
              }}
            >
              <HospitalIcon sx={{ fontSize: 36 }} />
            </Avatar>
            <Typography variant="h5" sx={{ fontWeight: 800 }}>
              NEXORA
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Clinical Prediction System
            </Typography>
          </Box>

          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
            Create your clinician account
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Full name"
              value={form.fullName}
              onChange={handleChange("fullName")}
              margin="normal"
              autoComplete="name"
              autoFocus
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Email address"
              type="email"
              value={form.email}
              onChange={handleChange("email")}
              margin="normal"
              autoComplete="email"
              disabled={loading}
            />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Organization (optional)"
                  value={form.organization}
                  onChange={handleChange("organization")}
                  margin="normal"
                  disabled={loading}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Specialty (optional)"
                  value={form.specialty}
                  onChange={handleChange("specialty")}
                  margin="normal"
                  disabled={loading}
                />
              </Grid>
            </Grid>
            <TextField
              fullWidth
              label="Password"
              type={showPassword ? "text" : "password"}
              value={form.password}
              onChange={handleChange("password")}
              margin="normal"
              autoComplete="new-password"
              disabled={loading}
              helperText="At least 8 characters, with a letter and a number"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              fullWidth
              label="Confirm password"
              type={showPassword ? "text" : "password"}
              value={form.confirmPassword}
              onChange={handleChange("confirmPassword")}
              margin="normal"
              autoComplete="new-password"
              disabled={loading}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              startIcon={<PersonAddIcon />}
              sx={{ mt: 3, mb: 1, py: 1.5, fontWeight: 700 }}
            >
              {loading ? "Creating account…" : "Create Account"}
            </Button>
          </Box>

          <Box sx={{ mt: 3, textAlign: "center" }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{" "}
              <MuiLink component={Link} to="/login" fontWeight={700}>
                Sign in
              </MuiLink>
            </Typography>
          </Box>

          <Box sx={{ mt: 2, textAlign: "center" }}>
            <Button
              variant="text"
              size="small"
              onClick={() => navigate("/")}
              sx={{ color: "text.secondary" }}
            >
              ← Back to Home
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SignUp;
