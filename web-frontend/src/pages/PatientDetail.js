import {
  ArrowBack as ArrowBackIcon,
  Assignment as AssignmentIcon,
  Autorenew as AutorenewIcon,
  CalendarToday as CalendarIcon,
  Download as DownloadIcon,
  Email as EmailIcon,
  Event as EventIcon,
  LocalHospital as HospitalIcon,
  LocationOn as LocationOnIcon,
  Medication as MedicationIcon,
  Phone as PhoneIcon,
  Science as ScienceIcon,
  Timeline as TimelineIcon,
  Warning as WarningIcon,
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
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Tab,
  Tabs,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip as ChartTooltip,
} from "chart.js";
import { useCallback, useEffect, useState } from "react";
import { Bar, Line } from "react-chartjs-2";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
);

const getRiskColor = (risk) => {
  if (risk >= 0.75) return "error";
  if (risk >= 0.4) return "warning";
  return "success";
};

const PatientDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [patient, setPatient] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMsg, setSnackbarMsg] = useState("");
  const [recomputing, setRecomputing] = useState(false);

  const fetchPatient = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPatientDetail(id);
      setPatient(data);
    } catch (err) {
      console.error(`Error fetching patient ${id}:`, err);
      setError("Failed to load patient details. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchPatient();
  }, [fetchPatient]);

  const handleRecomputeRisk = async () => {
    setRecomputing(true);
    try {
      const updated = await api.recomputeRisk(id);
      setPatient(updated);
      setSnackbarMsg(
        `Risk score refreshed: ${(updated.riskScore * 100).toFixed(0)}% (${updated.riskBand} risk).`,
      );
      setSnackbarOpen(true);
    } catch (err) {
      setSnackbarMsg("Failed to recompute risk score. Please try again.");
      setSnackbarOpen(true);
    } finally {
      setRecomputing(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: "100%", mt: 4 }}>
        <LinearProgress />
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 1, textAlign: "center" }}
        >
          Loading patient record…
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/patients")}
          sx={{ mb: 2 }}
        >
          Back
        </Button>
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  if (!patient) {
    return (
      <Box sx={{ mt: 4 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/patients")}
          sx={{ mb: 2 }}
        >
          Back
        </Button>
        <Alert severity="warning">Patient record not found for ID: {id}</Alert>
      </Box>
    );
  }

  // Chart data, built after null-guard so always safe
  const labResultsData = {
    labels: patient.labResults.map((l) => l.date),
    datasets: [
      {
        label: "Glucose (mg/dL)",
        data: patient.labResults.map((l) => l.glucose),
        borderColor: "#1976d2",
        backgroundColor: "rgba(25, 118, 210, 0.1)",
        tension: 0.4,
        yAxisID: "y",
      },
      {
        label: "Hemoglobin (g/dL)",
        data: patient.labResults.map((l) => l.hemoglobin),
        borderColor: "#9c27b0",
        backgroundColor: "rgba(156, 39, 176, 0.1)",
        tension: 0.4,
        yAxisID: "y1",
      },
    ],
  };

  const riskFactorsData = {
    labels: patient.riskFactors.map((f) => f.name),
    datasets: [
      {
        label: "Impact on Risk",
        data: patient.riskFactors.map((f) => f.impact),
        backgroundColor: patient.riskFactors.map((f) =>
          f.impact > 0.2
            ? "rgba(244, 67, 54, 0.7)"
            : f.impact > 0.1
              ? "rgba(255, 152, 0, 0.7)"
              : "rgba(76, 175, 80, 0.7)",
        ),
        borderRadius: 5,
      },
    ],
  };

  const handleDownload = () => {
    setSnackbarMsg("Downloading patient records… (demo)");
    setSnackbarOpen(true);
  };

  const handleSchedule = () => {
    setSnackbarMsg("Follow-up scheduling opened (demo)");
    setSnackbarOpen(true);
  };

  const initials = patient.name
    .split(" ")
    .map((n) => n[0])
    .join("");

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: "flex", alignItems: "center", gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/patients")}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Patient Details
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Sidebar: patient info card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                <Avatar
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: "primary.main",
                    fontSize: "1.5rem",
                    mr: 2,
                  }}
                >
                  {initials}
                </Avatar>
                <Box>
                  <Typography
                    variant="h5"
                    component="div"
                    sx={{ fontWeight: 600 }}
                  >
                    {patient.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ fontFamily: "monospace" }}
                  >
                    ID: {patient.id}
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <List dense>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CalendarIcon fontSize="small" color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Age / DOB"
                    secondary={`${patient.age} years (${patient.dob})`}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <AssignmentIcon fontSize="small" color="action" />
                  </ListItemIcon>
                  <ListItemText primary="Gender" secondary={patient.gender} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <HospitalIcon fontSize="small" color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Primary Diagnosis"
                    secondary={patient.primaryDiagnosis}
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <WarningIcon fontSize="small" color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Risk Score"
                    secondary={
                      <Chip
                        label={`${(patient.riskScore * 100).toFixed(0)}% Risk`}
                        color={getRiskColor(patient.riskScore)}
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                    }
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography
                variant="subtitle2"
                gutterBottom
                sx={{ fontWeight: 600 }}
              >
                Contact Information
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  mb: 0.5,
                  display: "flex",
                  alignItems: "center",
                  gap: 0.75,
                }}
              >
                <PhoneIcon fontSize="small" color="action" /> {patient.phone}
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  mb: 0.5,
                  display: "flex",
                  alignItems: "center",
                  gap: 0.75,
                }}
              >
                <EmailIcon fontSize="small" color="action" /> {patient.email}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ display: "flex", alignItems: "center", gap: 0.75 }}
              >
                <LocationOnIcon fontSize="small" color="action" />{" "}
                {patient.address}
              </Typography>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: "flex", gap: 1, flexDirection: "column" }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<AutorenewIcon />}
                  onClick={handleRecomputeRisk}
                  disabled={recomputing}
                >
                  {recomputing ? "Recomputing…" : "Recompute Risk Score"}
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownload}
                >
                  Download Records
                </Button>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<EventIcon />}
                  onClick={handleSchedule}
                >
                  Schedule Follow-up
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Main tabs */}
        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs
                value={activeTab}
                onChange={(_e, v) => setActiveTab(v)}
                aria-label="patient detail tabs"
                variant="scrollable"
                scrollButtons="auto"
              >
                <Tab label="Clinical Data" />
                <Tab label="Risk Analysis" />
                <Tab label="Medications" />
                <Tab label="Timeline" />
              </Tabs>
            </Box>

            {/* Tab 0: Clinical Data */}
            {activeTab === 0 && (
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Lab Results
                </Typography>
                <Box sx={{ height: 300, mb: 4 }}>
                  <Line
                    data={labResultsData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      interaction: { mode: "index", intersect: false },
                      plugins: { legend: { position: "top" } },
                      scales: {
                        y: {
                          beginAtZero: false,
                          title: { display: true, text: "Glucose (mg/dL)" },
                          position: "left",
                        },
                        y1: {
                          beginAtZero: false,
                          title: { display: true, text: "Hemoglobin (g/dL)" },
                          position: "right",
                          grid: { drawOnChartArea: false },
                        },
                      },
                    }}
                  />
                </Box>

                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Diagnoses
                </Typography>
                <List>
                  {patient.diagnoses.map((dx, i) => (
                    <ListItem
                      key={i}
                      divider={i < patient.diagnoses.length - 1}
                    >
                      <ListItemIcon>
                        <HospitalIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={dx.name}
                        secondary={`Diagnosed: ${dx.date} | ICD-10: ${dx.code}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}

            {/* Tab 1: Risk Analysis */}
            {activeTab === 1 && (
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Risk Factor Impact (SHAP)
                </Typography>
                <Box sx={{ height: 300, mb: 4 }}>
                  <Bar
                    data={riskFactorsData}
                    options={{
                      indexAxis: "y",
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false } },
                      scales: {
                        x: {
                          beginAtZero: true,
                          title: {
                            display: true,
                            text: "Impact on Risk Score",
                          },
                        },
                      },
                    }}
                  />
                </Box>

                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Recommended Interventions
                </Typography>
                <List>
                  {patient.interventions.map((iv, i) => (
                    <ListItem
                      key={i}
                      divider={i < patient.interventions.length - 1}
                    >
                      <ListItemIcon>
                        <ScienceIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={iv.name}
                        secondary={iv.description}
                      />
                      <Tooltip title={`Priority: ${iv.priority}`}>
                        <Chip
                          label={iv.priority}
                          color={
                            iv.priority === "High"
                              ? "error"
                              : iv.priority === "Medium"
                                ? "warning"
                                : "success"
                          }
                          size="small"
                          sx={{ ml: 1 }}
                        />
                      </Tooltip>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}

            {/* Tab 2: Medications */}
            {activeTab === 2 && (
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Current Medications
                </Typography>
                <List>
                  {patient.medications.map((med, i) => (
                    <ListItem
                      key={i}
                      divider={i < patient.medications.length - 1}
                    >
                      <ListItemIcon>
                        <MedicationIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Typography
                              variant="body1"
                              sx={{ fontWeight: 500 }}
                            >
                              {med.name}
                            </Typography>
                            <Chip
                              label={med.dosage}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={`Frequency: ${med.frequency}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}

            {/* Tab 3: Timeline */}
            {activeTab === 3 && (
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Clinical Timeline
                </Typography>
                <List>
                  {patient.timeline.map((event, i) => (
                    <ListItem
                      key={i}
                      divider={i < patient.timeline.length - 1}
                      sx={{
                        borderLeft:
                          i === patient.timeline.length - 1
                            ? "3px solid"
                            : "3px solid",
                        borderColor:
                          i === patient.timeline.length - 1
                            ? "primary.main"
                            : "divider",
                        pl: 2,
                        ml: 1,
                      }}
                    >
                      <ListItemIcon>
                        <TimelineIcon
                          color={
                            i === patient.timeline.length - 1
                              ? "primary"
                              : "action"
                          }
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Typography
                              variant="body1"
                              sx={{ fontWeight: 500 }}
                            >
                              {event.title}
                            </Typography>
                            {i === patient.timeline.length - 1 && (
                              <Chip
                                label="Latest"
                                size="small"
                                color="primary"
                              />
                            )}
                          </Box>
                        }
                        secondary={`${event.date}: ${event.description}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          severity="info"
          onClose={() => setSnackbarOpen(false)}
          sx={{ width: "100%" }}
        >
          {snackbarMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PatientDetail;
