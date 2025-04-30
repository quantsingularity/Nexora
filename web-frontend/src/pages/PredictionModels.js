import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Card, 
  CardContent, 
  CardHeader,
  Avatar,
  IconButton,
  Button,
  Divider,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
  Switch,
  FormControlLabel,
  TextField,
  MenuItem,
  Select,
  InputLabel,
  FormControl
} from '@mui/material';
import { 
  MoreVert as MoreVertIcon,
  Science as ScienceIcon,
  Tune as TuneIcon,
  CloudUpload as CloudUploadIcon,
  CloudDownload as CloudDownloadIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import api from '../services/api';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

const PredictionModels = () => {
  const [loading, setLoading] = useState(true);
  const [models, setModels] = useState([]);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const data = await api.getModels();
        setModels(data);
      } catch (error) {
        console.error('Error fetching models:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchModels();
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    );
  }

  const performanceData = {
    labels: ['Readmission', 'Mortality', 'LOS', 'Complications', 'ICU Transfer'],
    datasets: [
      {
        label: 'Current Model',
        data: [0.82, 0.78, 0.75, 0.81, 0.79],
        backgroundColor: 'rgba(25, 118, 210, 0.7)',
        borderRadius: 5,
      },
      {
        label: 'Previous Version',
        data: [0.79, 0.76, 0.72, 0.78, 0.75],
        backgroundColor: 'rgba(156, 39, 176, 0.7)',
        borderRadius: 5,
      },
    ],
  };

  const trainingData = {
    labels: ['0', '10', '20', '30', '40', '50', '60', '70', '80', '90', '100'],
    datasets: [
      {
        label: 'Training Loss',
        data: [0.68, 0.58, 0.51, 0.46, 0.42, 0.39, 0.37, 0.35, 0.34, 0.33, 0.32],
        borderColor: '#f44336',
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Validation Loss',
        data: [0.69, 0.60, 0.54, 0.50, 0.47, 0.45, 0.44, 0.43, 0.43, 0.42, 0.42],
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        tension: 0.4,
      },
    ],
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Prediction Models
        </Typography>
        <Button variant="contained" startIcon={<CloudUploadIcon />}>
          Deploy New Model
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Available Models" 
              action={
                <IconButton aria-label="refresh" onClick={() => api.getModels().then(data => setModels(data))}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <Divider />
            <CardContent>
              <List>
                {models.map((model, index) => (
                  <ListItem 
                    key={index} 
                    divider={index < models.length - 1}
                    secondaryAction={
                      <Chip 
                        icon={model.status === 'Active' ? <CheckCircleIcon /> : <ErrorIcon />}
                        label={model.status} 
                        color={model.status === 'Active' ? 'success' : 'default'}
                        size="small"
                      />
                    }
                  >
                    <ListItemIcon>
                      <ScienceIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={model.name} 
                      secondary={`Version: ${model.version} | Updated: ${model.lastUpdated}`} 
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange} aria-label="model tabs">
                <Tab label="Performance" />
                <Tab label="Training History" />
                <Tab label="Configuration" />
              </Tabs>
            </Box>
            
            {/* Performance Tab */}
            {activeTab === 0 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Performance Metrics
                </Typography>
                <Box sx={{ height: 300, mb: 4 }}>
                  <Bar 
                    data={performanceData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: true,
                          text: 'AUC Score by Prediction Task'
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 1,
                        },
                      },
                    }}
                  />
                </Box>
                
                <Typography variant="h6" gutterBottom>
                  Performance Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Accuracy
                        </Typography>
                        <Typography variant="h5" component="div">
                          0.85
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Precision
                        </Typography>
                        <Typography variant="h5" component="div">
                          0.78
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Recall
                        </Typography>
                        <Typography variant="h5" component="div">
                          0.81
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          F1 Score
                        </Typography>
                        <Typography variant="h5" component="div">
                          0.79
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </CardContent>
            )}
            
            {/* Training History Tab */}
            {activeTab === 1 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Training History
                </Typography>
                <Box sx={{ height: 300, mb: 4 }}>
                  <Line 
                    data={trainingData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: true,
                          text: 'Loss vs. Epochs'
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                        },
                        x: {
                          title: {
                            display: true,
                            text: 'Epochs'
                          }
                        }
                      },
                    }}
                  />
                </Box>
                
                <Typography variant="h6" gutterBottom>
                  Training Details
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Training Dataset
                        </Typography>
                        <Typography variant="body1">
                          120,000 patients (2020-2024)
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Validation Dataset
                        </Typography>
                        <Typography variant="body1">
                          30,000 patients (2024-2025)
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Training Time
                        </Typography>
                        <Typography variant="body1">
                          4.5 hours on GPU cluster
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Last Retrained
                        </Typography>
                        <Typography variant="body1">
                          March 15, 2025
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </CardContent>
            )}
            
            {/* Configuration Tab */}
            {activeTab === 2 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Configuration
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="model-type-label">Model Type</InputLabel>
                      <Select
                        labelId="model-type-label"
                        value="deepfm"
                        label="Model Type"
                      >
                        <MenuItem value="deepfm">DeepFM</MenuItem>
                        <MenuItem value="transformer">Transformer</MenuItem>
                        <MenuItem value="xgboost">XGBoost</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="prediction-task-label">Prediction Task</InputLabel>
                      <Select
                        labelId="prediction-task-label"
                        value="readmission"
                        label="Prediction Task"
                      >
                        <MenuItem value="readmission">30-day Readmission</MenuItem>
                        <MenuItem value="mortality">In-hospital Mortality</MenuItem>
                        <MenuItem value="los">Length of Stay</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Embedding Size"
                      type="number"
                      defaultValue={64}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Learning Rate"
                      type="number"
                      defaultValue={0.001}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Feature Settings
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Include Demographics"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Include Lab Results"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Include Medications"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Include Diagnoses"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Include Procedures"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Include Temporal Features"
                    />
                  </Grid>
                </Grid>
                
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                  <Button variant="outlined">
                    Reset to Defaults
                  </Button>
                  <Button variant="contained">
                    Save Configuration
                  </Button>
                </Box>
              </CardContent>
            )}
          </Card>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined" startIcon={<CloudDownloadIcon />}>
              Export Model
            </Button>
            <Button variant="contained" startIcon={<TuneIcon />}>
              Retrain Model
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PredictionModels;
