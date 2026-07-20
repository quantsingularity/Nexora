import {
  Add as AddIcon,
  ArrowForward as ArrowForwardIcon,
  FilterList as FilterListIcon,
  PersonSearch as PersonSearchIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api from "../services/api";

const getRiskColor = (risk) => {
  if (risk >= 0.75) return "error";
  if (risk >= 0.4) return "warning";
  return "success";
};

const getRiskLabel = (risk) => {
  if (risk >= 0.75) return "High";
  if (risk >= 0.4) return "Medium";
  return "Low";
};

const emptyPatientForm = {
  name: "",
  age: "",
  gender: "Female",
  diagnosis: "",
  mrn: "",
  phone: "",
  email: "",
  address: "",
};

const PatientList = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialRisk = searchParams.get("risk");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState(
    ["high", "medium", "low"].includes(initialRisk) ? initialRisk : "all",
  );
  const [genderFilter, setGenderFilter] = useState("all");
  const [orderBy, setOrderBy] = useState("name");
  const [order, setOrder] = useState("asc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [patients, setPatients] = useState([]);
  const [filterOpen, setFilterOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [addForm, setAddForm] = useState(emptyPatientForm);
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState("");
  const [snackbar, setSnackbar] = useState({ open: false, message: "" });

  const fetchPatients = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPatients();
      setPatients(data);
    } catch (err) {
      console.error("Error fetching patients:", err);
      setError("Failed to load patient list. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const handleSort = (field) => {
    const isAsc = orderBy === field && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(field);
    setPage(0);
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const handlePatientClick = (patientId) => {
    navigate(`/patients/${patientId}`);
  };

  const handleAddFormChange = (field) => (e) =>
    setAddForm((f) => ({ ...f, [field]: e.target.value }));

  const handleOpenAdd = () => {
    setAddForm(emptyPatientForm);
    setAddError("");
    setAddOpen(true);
  };

  const handleCloseAdd = () => {
    if (!addSubmitting) setAddOpen(false);
  };

  const handleSubmitAdd = async () => {
    if (!addForm.name.trim()) {
      setAddError("Patient name is required.");
      return;
    }
    setAddSubmitting(true);
    setAddError("");
    try {
      const created = await api.addPatient({
        name: addForm.name.trim(),
        age: addForm.age ? Number(addForm.age) : undefined,
        gender: addForm.gender || undefined,
        diagnosis: addForm.diagnosis.trim() || undefined,
        mrn: addForm.mrn.trim() || undefined,
        phone: addForm.phone.trim() || undefined,
        email: addForm.email.trim() || undefined,
        address: addForm.address.trim() || undefined,
      });
      setAddOpen(false);
      setSnackbar({
        open: true,
        message: `${created.name} was added with a computed risk score of ${(created.riskScore * 100).toFixed(0)}%.`,
      });
      fetchPatients();
    } catch (err) {
      setAddError(err.message || "Failed to add patient. Please try again.");
    } finally {
      setAddSubmitting(false);
    }
  };

  const filteredAndSorted = useMemo(() => {
    let result = patients.filter((p) => {
      const matchesSearch =
        !searchTerm ||
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (p.diagnosis || "").toLowerCase().includes(searchTerm.toLowerCase());

      const matchesRisk =
        riskFilter === "all" ||
        (riskFilter === "high" && p.riskScore >= 0.75) ||
        (riskFilter === "medium" && p.riskScore >= 0.4 && p.riskScore < 0.75) ||
        (riskFilter === "low" && p.riskScore < 0.4);

      const matchesGender =
        genderFilter === "all" ||
        p.gender.toLowerCase() === genderFilter.toLowerCase();

      return matchesSearch && matchesRisk && matchesGender;
    });

    result.sort((a, b) => {
      let valA = a[orderBy];
      let valB = b[orderBy];
      if (typeof valA === "string") valA = valA.toLowerCase();
      if (typeof valB === "string") valB = valB.toLowerCase();
      if (valA < valB) return order === "asc" ? -1 : 1;
      if (valA > valB) return order === "asc" ? 1 : -1;
      return 0;
    });

    return result;
  }, [patients, searchTerm, riskFilter, genderFilter, orderBy, order]);

  const paged = filteredAndSorted.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage,
  );

  const activeFilterCount = [
    riskFilter !== "all",
    genderFilter !== "all",
  ].filter(Boolean).length;

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
            Patient List
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {loading
              ? "Loading…"
              : `${filteredAndSorted.length} patient${filteredAndSorted.length !== 1 ? "s" : ""} found`}
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchPatients}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenAdd}
          >
            Add Patient
          </Button>
        </Box>
      </Box>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          {/* Search + Filter Bar */}
          <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2 }}>
            <TextField
              placeholder="Search by name, ID or diagnosis…"
              variant="outlined"
              size="small"
              fullWidth
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
            <Tooltip title="Filters">
              <IconButton
                onClick={() => setFilterOpen(true)}
                color={activeFilterCount > 0 ? "primary" : "default"}
              >
                <FilterListIcon />
                {activeFilterCount > 0 && (
                  <Box
                    sx={{
                      position: "absolute",
                      top: 4,
                      right: 4,
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      bgcolor: "primary.main",
                    }}
                  />
                )}
              </IconButton>
            </Tooltip>
          </Box>

          {/* Active filter chips */}
          {activeFilterCount > 0 && (
            <Box sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}>
              {riskFilter !== "all" && (
                <Chip
                  label={`Risk: ${riskFilter}`}
                  size="small"
                  onDelete={() => setRiskFilter("all")}
                  color="primary"
                  variant="outlined"
                />
              )}
              {genderFilter !== "all" && (
                <Chip
                  label={`Gender: ${genderFilter}`}
                  size="small"
                  onDelete={() => setGenderFilter("all")}
                  color="primary"
                  variant="outlined"
                />
              )}
              <Chip
                label="Clear all filters"
                size="small"
                onClick={() => {
                  setRiskFilter("all");
                  setGenderFilter("all");
                }}
                variant="outlined"
              />
            </Box>
          )}

          <Divider sx={{ my: 2 }} />

          {/* Error */}
          {!loading && error && (
            <Alert
              severity="error"
              action={
                <Button color="inherit" size="small" onClick={fetchPatients}>
                  Retry
                </Button>
              }
              sx={{ mb: 2 }}
            >
              {error}
            </Alert>
          )}

          {/* Loading */}
          {loading && <LinearProgress sx={{ mb: 2 }} />}

          {/* Table */}
          {!loading && !error && (
            <>
              <TableContainer component={Paper} elevation={0}>
                <Table sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>
                        <TableSortLabel
                          active={orderBy === "id"}
                          direction={orderBy === "id" ? order : "asc"}
                          onClick={() => handleSort("id")}
                        >
                          Patient ID
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={orderBy === "name"}
                          direction={orderBy === "name" ? order : "asc"}
                          onClick={() => handleSort("name")}
                        >
                          Name
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={orderBy === "age"}
                          direction={orderBy === "age" ? order : "asc"}
                          onClick={() => handleSort("age")}
                        >
                          Age
                        </TableSortLabel>
                      </TableCell>
                      <TableCell>Gender</TableCell>
                      <TableCell>Primary Diagnosis</TableCell>
                      <TableCell>Last Visit</TableCell>
                      <TableCell>
                        <TableSortLabel
                          active={orderBy === "riskScore"}
                          direction={orderBy === "riskScore" ? order : "asc"}
                          onClick={() => handleSort("riskScore")}
                        >
                          Risk Score
                        </TableSortLabel>
                      </TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paged.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                          <PersonSearchIcon
                            sx={{ fontSize: 48, color: "text.disabled", mb: 1 }}
                          />
                          <Typography variant="body1" color="text.secondary">
                            No patients match your search
                          </Typography>
                          <Button
                            size="small"
                            sx={{ mt: 1 }}
                            onClick={() => {
                              setSearchTerm("");
                              setRiskFilter("all");
                              setGenderFilter("all");
                            }}
                          >
                            Clear filters
                          </Button>
                        </TableCell>
                      </TableRow>
                    ) : (
                      paged.map((patient) => (
                        <TableRow
                          key={patient.id}
                          hover
                          sx={{ cursor: "pointer" }}
                          onClick={() => handlePatientClick(patient.id)}
                        >
                          <TableCell>
                            <Typography
                              variant="body2"
                              sx={{ fontFamily: "monospace" }}
                            >
                              {patient.id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: 500 }}
                            >
                              {patient.name}
                            </Typography>
                          </TableCell>
                          <TableCell>{patient.age}</TableCell>
                          <TableCell>{patient.gender}</TableCell>
                          <TableCell>{patient.diagnosis}</TableCell>
                          <TableCell>{patient.lastVisit}</TableCell>
                          <TableCell>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Chip
                                label={`${(patient.riskScore * 100).toFixed(0)}% ${getRiskLabel(patient.riskScore)}`}
                                color={getRiskColor(patient.riskScore)}
                                size="small"
                              />
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Tooltip title="View details">
                              <IconButton
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handlePatientClick(patient.id);
                                }}
                              >
                                <ArrowForwardIcon />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              <TablePagination
                rowsPerPageOptions={[5, 10, 25, 50]}
                component="div"
                count={filteredAndSorted.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={(_e, newPage) => setPage(newPage)}
                onRowsPerPageChange={(e) => {
                  setRowsPerPage(parseInt(e.target.value, 10));
                  setPage(0);
                }}
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* Filter Dialog */}
      <Dialog
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Filter Patients</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Risk Level</InputLabel>
            <Select
              value={riskFilter}
              label="Risk Level"
              onChange={(e) => setRiskFilter(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="high">High (≥ 75%)</MenuItem>
              <MenuItem value="medium">Medium (40–74%)</MenuItem>
              <MenuItem value="low">Low (&lt; 40%)</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Gender</InputLabel>
            <Select
              value={genderFilter}
              label="Gender"
              onChange={(e) => setGenderFilter(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="male">Male</MenuItem>
              <MenuItem value="female">Female</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setRiskFilter("all");
              setGenderFilter("all");
            }}
          >
            Clear
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              setPage(0);
              setFilterOpen(false);
            }}
          >
            Apply
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Patient Dialog */}
      <Dialog open={addOpen} onClose={handleCloseAdd} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Patient</DialogTitle>
        <DialogContent>
          {addError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {addError}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Full Name"
                value={addForm.name}
                onChange={handleAddFormChange("name")}
                required
                autoFocus
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Age"
                type="number"
                value={addForm.age}
                onChange={handleAddFormChange("age")}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={addForm.gender}
                  label="Gender"
                  onChange={handleAddFormChange("gender")}
                >
                  <MenuItem value="Female">Female</MenuItem>
                  <MenuItem value="Male">Male</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Primary Diagnosis"
                value={addForm.diagnosis}
                onChange={handleAddFormChange("diagnosis")}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="MRN (optional)"
                value={addForm.mrn}
                onChange={handleAddFormChange("mrn")}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={addForm.phone}
                onChange={handleAddFormChange("phone")}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                value={addForm.email}
                onChange={handleAddFormChange("email")}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Address"
                value={addForm.address}
                onChange={handleAddFormChange("address")}
              />
            </Grid>
          </Grid>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 2, display: "block" }}
          >
            A readmission risk score will be computed automatically using the
            deep_fm model as soon as the patient is created.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAdd} disabled={addSubmitting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmitAdd}
            disabled={addSubmitting}
          >
            {addSubmitting ? "Adding…" : "Add Patient"}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ open: false, message: "" })}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          severity="success"
          onClose={() => setSnackbar({ open: false, message: "" })}
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PatientList;
