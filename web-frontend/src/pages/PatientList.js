import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Button,
  Card,
  CardContent,
  Divider,
  LinearProgress
} from '@mui/material';
import { 
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Add as AddIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const PatientList = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        setLoading(true);
        const data = await api.getPatients();
        setPatients(data);
      } catch (error) {
        console.error('Error fetching patients:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatients();
  }, []);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const handlePatientClick = (patientId) => {
    navigate(`/patients/${patientId}`);
  };

  const filteredPatients = patients.filter(patient => 
    patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (patient.diagnosis && patient.diagnosis.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getRiskColor = (risk) => {
    if (risk >= 0.7) return 'error';
    if (risk >= 0.4) return 'warning';
    return 'success';
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Patient List
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          Add Patient
        </Button>
      </Box>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <TextField
              placeholder="Search patients..."
              variant="outlined"
              size="small"
              fullWidth
              value={searchTerm}
              onChange={handleSearchChange}
              sx={{ maxWidth: 500 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <IconButton>
              <FilterListIcon />
            </IconButton>
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          {loading ? (
            <Box sx={{ width: '100%', mt: 4, mb: 4 }}>
              <LinearProgress />
            </Box>
          ) : (
            <>
              <TableContainer component={Paper} elevation={0}>
                <Table sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Patient ID</TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Age</TableCell>
                      <TableCell>Gender</TableCell>
                      <TableCell>Primary Diagnosis</TableCell>
                      <TableCell>Last Visit</TableCell>
                      <TableCell>Risk Score</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredPatients.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} align="center">No patients found</TableCell>
                      </TableRow>
                    ) : (
                      filteredPatients
                        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                        .map((patient) => (
                          <TableRow key={patient.id} hover>
                            <TableCell>{patient.id}</TableCell>
                            <TableCell>{patient.name}</TableCell>
                            <TableCell>{patient.age}</TableCell>
                            <TableCell>{patient.gender}</TableCell>
                            <TableCell>{patient.diagnosis}</TableCell>
                            <TableCell>{patient.lastVisit}</TableCell>
                            <TableCell>
                              <Chip 
                                label={`${(patient.riskScore * 100).toFixed(0)}%`} 
                                color={getRiskColor(patient.riskScore)}
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="right">
                              <IconButton size="small" onClick={() => handlePatientClick(patient.id)}>
                                <ArrowForwardIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={filteredPatients.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
              />
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default PatientList;
