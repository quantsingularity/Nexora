import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
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
  LinearProgress
} from '@mui/material';
import { 
  MoreVert as MoreVertIcon,
  ArrowBack as ArrowBackIcon,
  CalendarToday as CalendarIcon,
  LocalHospital as HospitalIcon,
  Science as ScienceIcon,
  Assignment as AssignmentIcon,
  Medication as MedicationIcon,
  Timeline as TimelineIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

const PatientDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patient, setPatient] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    const fetchPatientDetail = async () => {
      try {
        setLoading(true);
        const data = await api.getPatientDetail(id);
        setPatient(data);
      } catch (error) {
        console.error(`Error fetching patient ${id}:`, error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatientDetail();
  }, [id]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleBack = () => {
    navigate('/patients');
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    );
  }

  if (!patient) {
    return (
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5">Patient not found</Typography>
      </Box>
    );
  }

  const getRiskColor = (risk) => {
    if (risk >= 0.7) return 'error';
    if (risk >= 0.4) return 'warning';
    return 'success';
  };

  const labResultsData = {
    labels: patient.labResults.map(lab => lab.date),
    datasets: [
      {
        label: 'Glucose (mg/dL)',
        data: patient.labResults.map(lab => lab.glucose),
        borderColor: '#1976d2',
        backgroundColor: 'rgba(25, 118, 210, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Hemoglobin (g/dL)',
        data: patient.labResults.map(lab => lab.hemoglobin),
        borderColor: '#9c27b0',
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        tension: 0.4,
      }
    ],
  };

  const riskFactorsData = {
    labels: patient.riskFactors.map(factor => factor.name),
    datasets: [
      {
        label: 'Impact on Risk',
        data: patient.riskFactors.map(factor => factor.impact),
        backgroundColor: patient.riskFactors.map(factor => 
          factor.impact > 0.2 ? 'rgba(244, 67, 54, 0.7)' : 
          factor.impact > 0.1 ? 'rgba(255, 152, 0, 0.7)' : 
          'rgba(76, 175, 80, 0.7)'
        ),
        borderRadius: 5,
      },
    ],
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center' }}>
        <Button 
          variant="outlined" 
          startIcon={<ArrowBackIcon />} 
          sx={{ mr: 2 }}
          onClick={handleBack}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Patient Details
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar 
                  sx={{ 
                    width: 64, 
                    height: 64, 
                    bgcolor: 'primary.main',
                    fontSize: '1.5rem',
                    mr: 2
                  }}
                >
                  {patient.name.split(' ').map(n => n[0]).join('')}
                </Avatar>
                <Box>
                  <Typography variant="h5" component="div">
                    {patient.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ID: {patient.id}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CalendarIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Age" 
                    secondary={`${patient.age} years (${patient.dob})`} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <AssignmentIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Gender" 
                    secondary={patient.gender} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <HospitalIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Primary Diagnosis" 
                    secondary={patient.primaryDiagnosis} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <WarningIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Risk Score" 
                    secondary={
                      <Chip 
                        label={`${(patient.riskScore * 100).toFixed(0)}%`} 
                        color={getRiskColor(patient.riskScore)}
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                    } 
                  />
                </ListItem>
              </List>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" gutterBottom>
                Contact Information
              </Typography>
              <Typography variant="body2" paragraph>
                Phone: {patient.phone}
              </Typography>
              <Typography variant="body2" paragraph>
                Email: {patient.email}
              </Typography>
              <Typography variant="body2">
                Address: {patient.address}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange} aria-label="patient tabs">
                <Tab label="Clinical Data" />
                <Tab label="Risk Analysis" />
                <Tab label="Medications" />
                <Tab label="Timeline" />
              </Tabs>
            </Box>
            
            {/* Clinical Data Tab */}
            {activeTab === 0 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Lab Results
                </Typography>
                <Box sx={{ height: 300, mb: 4 }}>
                  <Line 
                    data={labResultsData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                      },
                      scales: {
                        y: {
                          beginAtZero: false,
                        },
                      },
                    }}
                  />
                </Box>
                
                <Typography variant="h6" gutterBottom>
                  Diagnoses
                </Typography>
                <List>
                  {patient.diagnoses.map((diagnosis, index) => (
                    <ListItem key={index} divider={index < patient.diagnoses.length - 1}>
                      <ListItemIcon>
                        <HospitalIcon />
                      </ListItemIcon>
                      <ListItemText 
                        primary={diagnosis.name} 
                        secondary={`Diagnosed: ${diagnosis.date} | ICD-10: ${diagnosis.code}`} 
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}
            
            {/* Risk Analysis Tab */}
            {activeTab === 1 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Factors
                </Typography>
                <Box sx={{ height: 300, mb: 4 }}>
                  <Bar 
                    data={riskFactorsData} 
                    options={{
                      indexAxis: 'y',
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: false,
                        },
                      },
                      scales: {
                        x: {
                          beginAtZero: true,
                          title: {
                            display: true,
                            text: 'Impact on Risk Score'
                          }
                        },
                      },
                    }}
                  />
                </Box>
                
                <Typography variant="h6" gutterBottom>
                  Recommended Interventions
                </Typography>
                <List>
                  {patient.interventions.map((intervention, index) => (
                    <ListItem key={index} divider={index < patient.interventions.length - 1}>
                      <ListItemIcon>
                        <ScienceIcon />
                      </ListItemIcon>
                      <ListItemText 
                        primary={intervention.name} 
                        secondary={intervention.description} 
                      />
                      <Chip 
                        label={intervention.priority} 
                        color={
                          intervention.priority === 'High' ? 'error' : 
                          intervention.priority === 'Medium' ? 'warning' : 
                          'success'
                        }
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}
            
            {/* Medications Tab */}
            {activeTab === 2 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Medications
                </Typography>
                <List>
                  {patient.medications.map((medication, index) => (
                    <ListItem key={index} divider={index < patient.medications.length - 1}>
                      <ListItemIcon>
                        <MedicationIcon />
                      </ListItemIcon>
                      <ListItemText 
                        primary={medication.name} 
                        secondary={`Dosage: ${medication.dosage} | Frequency: ${medication.frequency}`} 
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}
            
            {/* Timeline Tab */}
            {activeTab === 3 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Clinical Timeline
                </Typography>
                <List>
                  {patient.timeline.map((event, index) => (
                    <ListItem key={index} divider={index < patient.timeline.length - 1}>
                      <ListItemIcon>
                        <TimelineIcon />
                      </ListItemIcon>
                      <ListItemText 
                        primary={event.title} 
                        secondary={`${event.date} | ${event.description}`} 
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            )}
          </Card>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined">
              Download Records
            </Button>
            <Button variant="contained">
              Schedule Follow-up
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PatientDetail;
