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
  LinearProgress,
  Chip
} from '@mui/material';
import { 
  MoreVert as MoreVertIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  People as PeopleIcon,
  Science as ScienceIcon,
  Assignment as AssignmentIcon
} from '@mui/icons-material';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title, BarElement } from 'chart.js';
import { Doughnut, Line, Bar } from 'react-chartjs-2';
import api from '../services/api';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title, BarElement);

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await api.getDashboardData();
        setDashboardData(data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  // Prepare chart data from API response
  const prepareChartData = () => {
    if (!dashboardData) return null;
    
    const patientRiskData = {
      labels: ['High Risk', 'Medium Risk', 'Low Risk'],
      datasets: [
        {
          data: [
            dashboardData.patientRiskDistribution.highRisk, 
            dashboardData.patientRiskDistribution.mediumRisk, 
            dashboardData.patientRiskDistribution.lowRisk
          ],
          backgroundColor: ['#f44336', '#ff9800', '#4caf50'],
          borderWidth: 0,
        },
      ],
    };

    const admissionsData = {
      labels: dashboardData.admissionsData.labels,
      datasets: [
        {
          label: 'Admissions',
          data: dashboardData.admissionsData.admissions,
          borderColor: '#1976d2',
          backgroundColor: 'rgba(25, 118, 210, 0.1)',
          tension: 0.4,
          fill: true,
        },
        {
          label: 'Readmissions',
          data: dashboardData.admissionsData.readmissions,
          borderColor: '#9c27b0',
          backgroundColor: 'rgba(156, 39, 176, 0.1)',
          tension: 0.4,
          fill: true,
        },
      ],
    };

    const modelPerformanceData = {
      labels: dashboardData.modelPerformance.labels,
      datasets: [
        {
          label: 'AUC',
          data: dashboardData.modelPerformance.scores,
          backgroundColor: 'rgba(25, 118, 210, 0.7)',
          borderRadius: 5,
        },
      ],
    };
    
    return {
      patientRiskData,
      admissionsData,
      modelPerformanceData
    };
  };

  const chartData = dashboardData ? prepareChartData() : null;

  const StatCard = ({ title, value, subtitle, icon, color, trend, trendValue }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Avatar sx={{ bgcolor: `${color}.light`, color: `${color}.dark` }}>
            {icon}
          </Avatar>
          {trend && (
            <Chip 
              icon={trend === 'up' ? <TrendingUpIcon /> : <TrendingDownIcon />} 
              label={`${trendValue}%`} 
              size="small"
              color={trend === 'up' ? 'success' : 'error'}
              variant="outlined"
            />
          )}
        </Box>
        <Typography variant="h4" component="div" sx={{ fontWeight: 'medium', mb: 0.5 }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Clinical Dashboard
        </Typography>
        <Button variant="contained" startIcon={<AssignmentIcon />}>
          Generate Report
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ width: '100%', mt: 4 }}>
          <LinearProgress />
        </Box>
      ) : dashboardData && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard 
                title="Active Patients" 
                value={dashboardData.stats.activePatients.toLocaleString()} 
                subtitle="Total patients under care"
                icon={<PeopleIcon />}
                color="primary"
                trend="up"
                trendValue="12"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard 
                title="High Risk Patients" 
                value={dashboardData.stats.highRiskPatients.toLocaleString()} 
                subtitle={`${(dashboardData.stats.highRiskPatients / dashboardData.stats.activePatients * 100).toFixed(1)}% of total patients`}
                icon={<TrendingUpIcon />}
                color="error"
                trend="down"
                trendValue="3"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard 
                title="Avg. Length of Stay" 
                value={`${dashboardData.stats.avgLengthOfStay} days`} 
                subtitle="Last 30 days"
                icon={<AssignmentIcon />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard 
                title="Active Models" 
                value={dashboardData.stats.activeModels} 
                subtitle="Last updated: Today"
                icon={<ScienceIcon />}
                color="success"
              />
            </Grid>
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card sx={{ height: '100%' }}>
                <CardHeader 
                  title="Admissions & Readmissions Trend" 
                  action={
                    <IconButton aria-label="settings">
                      <MoreVertIcon />
                    </IconButton>
                  }
                />
                <Divider />
                <CardContent>
                  <Box sx={{ height: 300, p: 1 }}>
                    <Line 
                      data={chartData.admissionsData} 
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
                            beginAtZero: true,
                          },
                        },
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%' }}>
                <CardHeader 
                  title="Patient Risk Distribution" 
                  action={
                    <IconButton aria-label="settings">
                      <MoreVertIcon />
                    </IconButton>
                  }
                />
                <Divider />
                <CardContent>
                  <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Doughnut 
                      data={chartData.patientRiskData} 
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                          },
                        },
                        cutout: '70%',
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardHeader 
                  title="Model Performance Metrics" 
                  action={
                    <IconButton aria-label="settings">
                      <MoreVertIcon />
                    </IconButton>
                  }
                />
                <Divider />
                <CardContent>
                  <Box sx={{ height: 250, p: 1 }}>
                    <Bar 
                      data={chartData.modelPerformanceData} 
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            display: false,
                          },
                        },
                        scales: {
                          y: {
                            beginAtZero: true,
                            max: 1,
                            title: {
                              display: true,
                              text: 'AUC Score'
                            }
                          },
                        },
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default Dashboard;
