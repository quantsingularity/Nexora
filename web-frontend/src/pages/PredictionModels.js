import {
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Science as ScienceIcon,
} from "@mui/icons-material";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip as ChartTooltip,
} from "chart.js";
import { useCallback, useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import api from "../services/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
);

const MODEL_DESCRIPTIONS = {
  deep_fm:
    "Factorization-machine deep network trained for 30-day readmission risk from demographics, diagnoses, and utilization history.",
  survival_analysis:
    "Time-to-event survival model estimating readmission likelihood over a patient's follow-up window.",
  transformer_model:
    "Sequence transformer trained on longitudinal clinical events for higher-order temporal risk patterns.",
};

const PredictionModels = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [performance, setPerformance] = useState(null);

  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [manualPatientId, setManualPatientId] = useState("");
  const [running, setRunning] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionError, setPredictionError] = useState(null);

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getModels();
      setModels(data);
      setSelectedModel((prev) => prev || data[0] || null);
    } catch (err) {
      setError(err.message || "Failed to load models. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  useEffect(() => {
    api
      .getDashboardData()
      .then((d) => setPerformance(d.modelPerformance))
      .catch(() => setPerformance(null));
    api
      .getPatients({ pageSize: 100 })
      .then(setPatients)
      .catch(() => setPatients([]));
  }, []);

  const handleRunPrediction = async () => {
    if (!selectedModel) return;
    const patientId = selectedPatient?.id || manualPatientId.trim();
    if (!patientId) {
      setPredictionError("Choose a patient or enter a patient ID.");
      return;
    }
    setRunning(true);
    setPredictionError(null);
    setPredictionResult(null);
    try {
      const demographics = selectedPatient
        ? {
            age: selectedPatient.age,
            gender: selectedPatient.gender,
            diagnosis: selectedPatient.diagnosis,
          }
        : {};
      const result = await api.makePrediction(selectedModel.name, undefined, {
        patient_id: patientId,
        demographics,
        clinical_events: [],
      });
      setPredictionResult(result);
    } catch (err) {
      setPredictionError(err.message || "Prediction request failed.");
    } finally {
      setRunning(false);
    }
  };

  const performanceChart = performance
    ? {
        labels: performance.labels,
        datasets: [
          {
            label: "AUC",
            data: performance.scores,
            backgroundColor: "rgba(37, 99, 235, 0.75)",
            borderRadius: 6,
          },
        ],
      }
    : null;

  if (loading) {
    return (
      <Box sx={{ width: "100%", mt: 4 }}>
        <LinearProgress />
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 1, textAlign: "center" }}
        >
          Loading prediction models…
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={fetchModels}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Prediction Models
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Models registered in the ml_core model registry, available for live
          scoring
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Model list */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader
              title="Available Models"
              action={
                <IconButton aria-label="refresh" onClick={fetchModels}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <Divider />
            <List disablePadding>
              {models.map((model) => (
                <ListItemButton
                  key={model.name}
                  selected={selectedModel?.name === model.name}
                  onClick={() => setSelectedModel(model)}
                  sx={{ py: 1.5, px: 2 }}
                >
                  <ListItemIcon>
                    <ScienceIcon
                      color={
                        selectedModel?.name === model.name
                          ? "primary"
                          : "action"
                      }
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={model.displayName}
                    secondary={`Version ${model.version}`}
                  />
                  <Chip
                    icon={<CheckCircleIcon />}
                    label={model.status}
                    color="success"
                    size="small"
                  />
                </ListItemButton>
              ))}
              {models.length === 0 && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ p: 3 }}
                >
                  No models are currently registered.
                </Typography>
              )}
            </List>
          </Card>
        </Grid>

        {/* Detail panel */}
        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs value={activeTab} onChange={(_e, v) => setActiveTab(v)}>
                <Tab label="Overview" />
                <Tab label="Run Prediction" />
              </Tabs>
            </Box>

            {activeTab === 0 && (
              <CardContent>
                {selectedModel ? (
                  <>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {selectedModel.displayName}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 3 }}
                    >
                      {MODEL_DESCRIPTIONS[selectedModel.name] ||
                        "Registered clinical prediction model."}
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography
                              variant="subtitle2"
                              color="text.secondary"
                            >
                              Version
                            </Typography>
                            <Typography variant="h6">
                              {selectedModel.version}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography
                              variant="subtitle2"
                              color="text.secondary"
                            >
                              Status
                            </Typography>
                            <Typography variant="h6" color="success.main">
                              {selectedModel.status}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </>
                ) : (
                  <Typography color="text.secondary">
                    Select a model from the list to see details.
                  </Typography>
                )}

                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{ fontWeight: 600, mt: 1 }}
                >
                  Model Performance (AUC)
                </Typography>
                {performanceChart ? (
                  <Box sx={{ height: 260 }}>
                    <Bar
                      data={performanceChart}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true, max: 1 } },
                      }}
                    />
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Performance metrics unavailable.
                  </Typography>
                )}
              </CardContent>
            )}

            {activeTab === 1 && (
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Run a Live Prediction
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 3 }}
                >
                  Calls the real <code>/predict</code> endpoint using{" "}
                  <strong>
                    {selectedModel?.displayName || "the selected model"}
                  </strong>
                  .
                </Typography>

                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} sm={7}>
                    <Autocomplete
                      options={patients}
                      getOptionLabel={(p) => `${p.name} (${p.id})`}
                      value={selectedPatient}
                      onChange={(_e, val) => setSelectedPatient(val)}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Search existing patient"
                        />
                      )}
                    />
                  </Grid>
                  <Grid item xs={12} sm={5}>
                    <TextField
                      fullWidth
                      label="…or enter a patient ID"
                      value={manualPatientId}
                      onChange={(e) => {
                        setManualPatientId(e.target.value);
                        setSelectedPatient(null);
                      }}
                      disabled={!!selectedPatient}
                    />
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleRunPrediction}
                  disabled={running || !selectedModel}
                  sx={{ mt: 3 }}
                >
                  {running ? "Running…" : "Run Prediction"}
                </Button>

                {predictionError && (
                  <Alert severity="error" sx={{ mt: 3 }}>
                    {predictionError}
                  </Alert>
                )}

                {predictionResult && (
                  <Box sx={{ mt: 3 }}>
                    <Divider sx={{ mb: 2 }} />
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography
                              variant="subtitle2"
                              color="text.secondary"
                            >
                              Risk Score
                            </Typography>
                            <Typography
                              variant="h4"
                              color="primary.main"
                              sx={{ fontWeight: 700 }}
                            >
                              {(
                                (predictionResult.predictions?.risk_score ??
                                  predictionResult.predictions?.risk ??
                                  0) * 100
                              ).toFixed(1)}
                              %
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography
                              variant="subtitle2"
                              color="text.secondary"
                            >
                              Top Contributing Features
                            </Typography>
                            <Box
                              sx={{
                                mt: 1,
                                display: "flex",
                                gap: 0.5,
                                flexWrap: "wrap",
                              }}
                            >
                              {(
                                predictionResult.predictions?.top_features || []
                              ).map((f) => (
                                <Chip key={f} label={f} size="small" />
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                    <Typography
                      variant="caption"
                      color="text.disabled"
                      sx={{ mt: 2, display: "block" }}
                    >
                      Request ID: {predictionResult.request_id} · Model:{" "}
                      {predictionResult.model_name}{" "}
                      {predictionResult.model_version} ·{" "}
                      {predictionResult.timestamp}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PredictionModels;
