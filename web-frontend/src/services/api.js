import axios from 'axios';

// Mock API service for development
const useMockData = true;

// Generate mock patient data
const generateMockPatients = () => {
  const diagnoses = [
    'Hypertension', 'Type 2 Diabetes', 'Congestive Heart Failure', 
    'COPD', 'Asthma', 'Pneumonia', 'COVID-19', 'Stroke', 
    'Myocardial Infarction', 'Chronic Kidney Disease'
  ];
  
  const firstNames = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 
    'Linda', 'William', 'Elizabeth', 'David', 'Susan', 'Richard', 'Jessica', 
    'Joseph', 'Sarah', 'Thomas', 'Karen', 'Charles', 'Nancy'
  ];
  
  const lastNames = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
  ];
  
  const patients = [];
  
  for (let i = 1; i <= 50; i++) {
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    
    patients.push({
      id: `P${String(i).padStart(5, '0')}`,
      name: `${firstName} ${lastName}`,
      age: Math.floor(Math.random() * 50) + 25,
      gender: Math.random() > 0.5 ? 'Male' : 'Female',
      diagnosis: diagnoses[Math.floor(Math.random() * diagnoses.length)],
      lastVisit: new Date(Date.now() - Math.floor(Math.random() * 90) * 24 * 60 * 60 * 1000).toLocaleDateString(),
      riskScore: Math.random()
    });
  }
  
  return patients;
};

// Generate mock patient detail
const generateMockPatientDetail = (id) => {
  return {
    id: id,
    name: "John Smith",
    age: 58,
    dob: "1967-05-12",
    gender: "Male",
    primaryDiagnosis: "Type 2 Diabetes",
    riskScore: 0.72,
    phone: "(555) 123-4567",
    email: "john.smith@example.com",
    address: "123 Main St, Anytown, CA 94123",
    
    labResults: [
      { date: "2025-01-15", glucose: 142, hemoglobin: 13.2 },
      { date: "2025-02-01", glucose: 156, hemoglobin: 12.9 },
      { date: "2025-02-15", glucose: 168, hemoglobin: 12.7 },
      { date: "2025-03-01", glucose: 145, hemoglobin: 12.8 },
      { date: "2025-03-15", glucose: 152, hemoglobin: 13.0 },
      { date: "2025-04-01", glucose: 138, hemoglobin: 13.1 }
    ],
    
    diagnoses: [
      { name: "Type 2 Diabetes", date: "2020-03-15", code: "E11.9" },
      { name: "Hypertension", date: "2021-06-22", code: "I10" },
      { name: "Hyperlipidemia", date: "2021-06-22", code: "E78.5" },
      { name: "Diabetic Neuropathy", date: "2023-11-08", code: "E11.40" }
    ],
    
    riskFactors: [
      { name: "Previous Hospitalizations", impact: 0.28 },
      { name: "HbA1c > 8.0", impact: 0.22 },
      { name: "Medication Non-adherence", impact: 0.18 },
      { name: "Age > 55", impact: 0.15 },
      { name: "Hypertension", impact: 0.12 },
      { name: "Hyperlipidemia", impact: 0.05 }
    ],
    
    interventions: [
      { 
        name: "Medication Adherence Program", 
        description: "Enroll patient in medication adherence monitoring program with weekly check-ins", 
        priority: "High" 
      },
      { 
        name: "Diabetes Education", 
        description: "Schedule comprehensive diabetes self-management education session", 
        priority: "Medium" 
      },
      { 
        name: "Nutrition Consultation", 
        description: "Refer to dietitian for medical nutrition therapy", 
        priority: "Medium" 
      },
      { 
        name: "Remote Monitoring", 
        description: "Provide glucose monitoring device with data transmission capabilities", 
        priority: "High" 
      }
    ],
    
    medications: [
      { name: "Metformin", dosage: "1000mg", frequency: "Twice daily" },
      { name: "Lisinopril", dosage: "10mg", frequency: "Once daily" },
      { name: "Atorvastatin", dosage: "20mg", frequency: "Once daily at bedtime" },
      { name: "Aspirin", dosage: "81mg", frequency: "Once daily" }
    ],
    
    timeline: [
      { 
        title: "Initial Diagnosis", 
        date: "2020-03-15", 
        description: "Diagnosed with Type 2 Diabetes" 
      },
      { 
        title: "Hospitalization", 
        date: "2021-06-20", 
        description: "Admitted for hyperglycemia, diagnosed with hypertension and hyperlipidemia" 
      },
      { 
        title: "Medication Change", 
        date: "2022-08-12", 
        description: "Increased Metformin dosage to 1000mg BID" 
      },
      { 
        title: "Specialist Referral", 
        date: "2023-11-08", 
        description: "Referred to neurologist, diagnosed with diabetic neuropathy" 
      },
      { 
        title: "Emergency Visit", 
        date: "2024-12-30", 
        description: "ER visit for hypoglycemic episode" 
      },
      { 
        title: "Follow-up Visit", 
        date: "2025-01-15", 
        description: "Regular check-up, HbA1c: 8.2%" 
      },
      { 
        title: "Latest Visit", 
        date: "2025-04-01", 
        description: "Follow-up visit, adjusted medication regimen" 
      }
    ]
  };
};

// Generate mock models
const generateMockModels = () => {
  return [
    {
      name: "Readmission Risk Predictor",
      version: "1.2.0",
      lastUpdated: "2025-03-15",
      status: "Active"
    },
    {
      name: "Mortality Prediction Model",
      version: "1.0.5",
      lastUpdated: "2025-02-28",
      status: "Active"
    },
    {
      name: "Length of Stay Estimator",
      version: "0.9.8",
      lastUpdated: "2025-03-10",
      status: "Active"
    },
    {
      name: "Complication Risk Model",
      version: "1.1.2",
      lastUpdated: "2025-03-05",
      status: "Active"
    },
    {
      name: "ICU Transfer Predictor",
      version: "0.8.5",
      lastUpdated: "2025-02-20",
      status: "Inactive"
    }
  ];
};

// API base URL
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check endpoint
export const checkHealth = async () => {
  if (useMockData) {
    return { status: "healthy", timestamp: new Date().toISOString() };
  }
  
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

// Get list of available models
export const getModels = async () => {
  if (useMockData) {
    return generateMockModels();
  }
  
  try {
    const response = await api.get('/models');
    return response.data.models;
  } catch (error) {
    console.error('Failed to fetch models:', error);
    throw error;
  }
};

// Get list of patients
export const getPatients = async () => {
  if (useMockData) {
    return generateMockPatients();
  }
  
  try {
    const response = await api.get('/patients');
    return response.data.patients;
  } catch (error) {
    console.error('Failed to fetch patients:', error);
    throw error;
  }
};

// Get patient details
export const getPatientDetail = async (patientId) => {
  if (useMockData) {
    return generateMockPatientDetail(patientId);
  }
  
  try {
    const response = await api.get(`/patients/${patientId}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch patient ${patientId}:`, error);
    throw error;
  }
};

// Make prediction for a patient
export const makePrediction = async (modelName, modelVersion, patientData) => {
  if (useMockData) {
    return {
      request_id: `req_${Date.now()}`,
      model_name: modelName,
      model_version: modelVersion || "latest",
      timestamp: new Date().toISOString(),
      predictions: {
        risk: 0.75,
        top_features: ["age", "previous_admissions", "diabetes"],
        cohort_size: 120,
        shap_features: ["age", "previous_admissions", "diabetes", "hypertension", "heart_disease"],
        shap_values: [0.3, 0.25, 0.2, 0.15, 0.1]
      },
      explanations: {
        method: "SHAP", 
        values: [0.3, 0.25, 0.2, 0.15, 0.1]
      },
      uncertainty: {
        confidence_interval: [0.65, 0.85]
      }
    };
  }
  
  try {
    const response = await api.post('/predict', {
      model_name: modelName,
      model_version: modelVersion,
      patient_data: patientData,
    });
    return response.data;
  } catch (error) {
    console.error('Prediction failed:', error);
    throw error;
  }
};

// Get prediction from FHIR patient data
export const getPredictionFromFHIR = async (patientId, modelName, modelVersion) => {
  if (useMockData) {
    return {
      request_id: `fhir_${patientId}_${Date.now()}`,
      model_name: modelName,
      model_version: modelVersion || "latest",
      timestamp: new Date().toISOString(),
      predictions: {
        risk: 0.65,
        top_features: ["age", "previous_admissions", "diabetes"]
      }
    };
  }
  
  try {
    const response = await api.post(`/fhir/patient/${patientId}/predict`, null, {
      params: {
        model_name: modelName,
        model_version: modelVersion,
      },
    });
    return response.data;
  } catch (error) {
    console.error('FHIR prediction failed:', error);
    throw error;
  }
};

// Get dashboard data
export const getDashboardData = async () => {
  if (useMockData) {
    return {
      stats: {
        activePatients: 1284,
        highRiskPatients: 256,
        avgLengthOfStay: 4.2,
        activeModels: 5
      },
      patientRiskDistribution: {
        highRisk: 25,
        mediumRisk: 45,
        lowRisk: 30
      },
      admissionsData: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        admissions: [65, 59, 80, 81, 56, 55],
        readmissions: [28, 48, 40, 19, 36, 27]
      },
      modelPerformance: {
        labels: ['Readmission', 'Mortality', 'LOS', 'Complications'],
        scores: [0.82, 0.78, 0.75, 0.81]
      }
    };
  }
  
  try {
    const response = await api.get('/dashboard');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
    throw error;
  }
};

export default {
  checkHealth,
  getModels,
  getPatients,
  getPatientDetail,
  makePrediction,
  getPredictionFromFHIR,
  getDashboardData
};
