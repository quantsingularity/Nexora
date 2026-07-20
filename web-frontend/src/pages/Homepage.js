import {
  Analytics as AnalyticsIcon,
  ArrowForward as ArrowForwardIcon,
  Favorite as HeartIcon,
  LocalHospital as HospitalIcon,
  People as PeopleIcon,
  Science as ScienceIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
} from "@mui/icons-material";
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Grid,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { brand } from "../assets/styles/theme";
import { useAuth } from "../context/AuthContext";

const features = [
  {
    icon: <ScienceIcon fontSize="large" />,
    title: "AI-Powered Predictions",
    description:
      "Advanced machine learning models trained on millions of patient records to predict readmission risk, mortality, and length of stay with state-of-the-art accuracy.",
    color: "primary",
  },
  {
    icon: <PeopleIcon fontSize="large" />,
    title: "Patient Risk Stratification",
    description:
      "Automatically stratify your patient population into risk tiers. Prioritize care interventions for high-risk patients before adverse events occur.",
    color: "error",
  },
  {
    icon: <TimelineIcon fontSize="large" />,
    title: "Clinical Timeline Tracking",
    description:
      "Comprehensive longitudinal patient histories with lab results, diagnoses, medications, and clinical events, all in one unified view.",
    color: "info",
  },
  {
    icon: <AnalyticsIcon fontSize="large" />,
    title: "Real-Time Analytics",
    description:
      "Live dashboards with admissions trends, model performance metrics, and population health insights updated in real time.",
    color: "success",
  },
  {
    icon: <SecurityIcon fontSize="large" />,
    title: "HIPAA Compliant",
    description:
      "Built from the ground up with healthcare compliance in mind. All data is encrypted, audited, and handled according to HIPAA regulations.",
    color: "warning",
  },
  {
    icon: <SpeedIcon fontSize="large" />,
    title: "Fast & Scalable",
    description:
      "Handles thousands of concurrent patients without performance degradation. Designed for enterprise hospital systems and large healthcare networks.",
    color: "secondary",
  },
];

const stats = [
  { value: "98.5%", label: "System Uptime" },
  { value: "0.82", label: "Avg. AUC Score" },
  { value: "50k+", label: "Patients Monitored" },
  { value: "5", label: "Active ML Models" },
];

const Homepage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const primaryDestination = isAuthenticated ? "/dashboard" : "/signup";

  return (
    <Box sx={{ bgcolor: "background.default", minHeight: "100vh" }}>
      {/* Top Navigation */}
      <Box
        sx={{
          bgcolor: "white",
          borderBottom: "1px solid rgba(0,0,0,0.08)",
          px: 4,
          py: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 100,
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <Avatar sx={{ bgcolor: "primary.main", width: 36, height: 36 }}>
            <HospitalIcon fontSize="small" />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.1 }}>
              NEXORA
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Clinical Prediction System
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          {isAuthenticated ? (
            <Button
              variant="contained"
              onClick={() => navigate("/dashboard")}
              endIcon={<ArrowForwardIcon />}
            >
              Go to Dashboard
            </Button>
          ) : (
            <>
              <Button
                variant="text"
                color="inherit"
                onClick={() => navigate("/login")}
              >
                Sign In
              </Button>
              <Button
                variant="contained"
                onClick={() => navigate("/signup")}
                endIcon={<ArrowForwardIcon />}
              >
                Get Started
              </Button>
            </>
          )}
        </Box>
      </Box>

      {/* Hero Section */}
      <Box
        sx={{
          background: brand.gradient,
          color: "white",
          py: { xs: 8, md: 14 },
          px: 4,
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Decorative circles */}
        <Box
          sx={{
            position: "absolute",
            top: -80,
            right: -80,
            width: 400,
            height: 400,
            borderRadius: "50%",
            bgcolor: "rgba(255,255,255,0.05)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            bottom: -100,
            left: -60,
            width: 300,
            height: 300,
            borderRadius: "50%",
            bgcolor: "rgba(255,255,255,0.05)",
          }}
        />

        <Container maxWidth="lg">
          <Box sx={{ maxWidth: 720, position: "relative" }}>
            <Chip
              label="AI-Powered Healthcare Intelligence"
              sx={{
                bgcolor: "rgba(255,255,255,0.15)",
                color: "white",
                mb: 3,
                fontWeight: 600,
                border: "1px solid rgba(255,255,255,0.3)",
              }}
              icon={<HeartIcon sx={{ color: "white !important" }} />}
            />
            <Typography
              variant="h2"
              component="h1"
              sx={{
                fontWeight: 800,
                fontSize: { xs: "2.2rem", md: "3.5rem" },
                lineHeight: 1.15,
                mb: 3,
              }}
            >
              Predict Clinical Outcomes.{" "}
              <Box component="span" sx={{ color: "#bbdefb" }}>
                Improve Patient Care.
              </Box>
            </Typography>
            <Typography
              variant="h6"
              sx={{
                opacity: 0.9,
                fontWeight: 400,
                mb: 5,
                lineHeight: 1.6,
                maxWidth: 580,
              }}
            >
              Nexora uses advanced machine learning to help clinicians
              proactively identify high-risk patients, reduce readmissions, and
              optimize care pathways, all from a single intelligent platform.
            </Typography>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate(primaryDestination)}
                endIcon={<ArrowForwardIcon />}
                sx={{
                  bgcolor: "white",
                  color: "primary.dark",
                  fontWeight: 700,
                  px: 4,
                  py: 1.5,
                  "&:hover": {
                    bgcolor: "grey.100",
                  },
                }}
              >
                {isAuthenticated ? "Open Dashboard" : "Get Started Free"}
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() =>
                  navigate(isAuthenticated ? "/patients" : "/login")
                }
                sx={{
                  borderColor: "rgba(255,255,255,0.5)",
                  color: "white",
                  px: 4,
                  py: 1.5,
                  "&:hover": {
                    borderColor: "white",
                    bgcolor: "rgba(255,255,255,0.1)",
                  },
                }}
              >
                {isAuthenticated ? "View Patients" : "Sign In"}
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Stats Bar */}
      <Box
        sx={{ bgcolor: "white", borderBottom: "1px solid rgba(0,0,0,0.08)" }}
      >
        <Container maxWidth="lg">
          <Grid container>
            {stats.map((stat, i) => (
              <Grid item xs={6} md={3} key={i}>
                <Box
                  sx={{
                    py: 4,
                    px: 3,
                    textAlign: "center",
                    borderRight:
                      i < stats.length - 1
                        ? "1px solid rgba(0,0,0,0.08)"
                        : "none",
                  }}
                >
                  <Typography
                    variant="h3"
                    sx={{ fontWeight: 800, color: "primary.main" }}
                  >
                    {stat.value}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stat.label}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Box sx={{ textAlign: "center", mb: 8 }}>
          <Typography
            variant="overline"
            color="primary"
            sx={{ fontWeight: 700, letterSpacing: 2 }}
          >
            CAPABILITIES
          </Typography>
          <Typography variant="h3" sx={{ fontWeight: 700, mt: 1, mb: 2 }}>
            Everything you need to transform patient care
          </Typography>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 600, mx: "auto", fontWeight: 400 }}
          >
            A comprehensive suite of clinical intelligence tools designed
            specifically for modern healthcare teams.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: "100%",
                  transition: "transform 0.2s, box-shadow 0.2s",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: "0px 8px 24px rgba(0,0,0,0.12)",
                  },
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Avatar
                    sx={{
                      bgcolor: `${feature.color}.light`,
                      color: `${feature.color}.dark`,
                      width: 56,
                      height: 56,
                      mb: 2,
                    }}
                  >
                    {feature.icon}
                  </Avatar>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                    {feature.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    lineHeight={1.7}
                  >
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box
        sx={{
          bgcolor: "grey.900",
          color: "white",
          py: 10,
          textAlign: "center",
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
            Ready to improve patient outcomes?
          </Typography>
          <Typography
            variant="h6"
            sx={{ opacity: 0.7, mb: 5, fontWeight: 400 }}
          >
            Access the full clinical prediction platform right now. No setup
            required.
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate(primaryDestination)}
            endIcon={<ArrowForwardIcon />}
            sx={{ px: 5, py: 1.8, fontSize: "1.1rem", fontWeight: 700 }}
          >
            {isAuthenticated ? "Launch Dashboard" : "Create Free Account"}
          </Button>
        </Container>
      </Box>

      {/* Footer */}
      <Box
        sx={{
          bgcolor: "white",
          borderTop: "1px solid rgba(0,0,0,0.08)",
          py: 4,
          px: 4,
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Avatar sx={{ bgcolor: "primary.main", width: 28, height: 28 }}>
                <HospitalIcon sx={{ fontSize: 16 }} />
              </Avatar>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                NEXORA Clinical Prediction System
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              © {new Date().getFullYear()} Nexora Health. All rights reserved. |{" "}
              <Box
                component="span"
                sx={{ color: "primary.main", cursor: "pointer" }}
              >
                Privacy Policy
              </Box>{" "}
              |{" "}
              <Box
                component="span"
                sx={{ color: "primary.main", cursor: "pointer" }}
              >
                Terms of Service
              </Box>
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default Homepage;
