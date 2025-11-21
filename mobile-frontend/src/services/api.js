import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Define the base URL for the API. Replace with the actual deployed backend URL.
// For local testing, if the backend runs on the host machine,
// use the host machine's IP address or a service like ngrok.
// For now, using a placeholder.
const API_BASE_URL = "http://localhost:8000"; // Replace with actual backend URL

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Optional: Add interceptor to include auth token if needed
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem("userToken");
    if (token) {
      // Assuming the backend expects a Bearer token
      // config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// API Service Functions

const getHealth = () => {
  return apiClient.get("/health");
};

const listModels = () => {
  return apiClient.get("/models");
};

const getPatients = async () => {
  // This endpoint doesn't exist in the provided backend API.
  // We'll keep the mock data logic in HomeScreen for now,
  // or adapt if a patient list endpoint is available.
  console.warn(
    "getPatients function called, but no backend endpoint defined. Using mock data.",
  );
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 500));
  // Return mock data
  return [
    {
      id: "p001",
      name: "John Doe",
      age: 65,
      risk: 0.75,
      last_update: "2024-04-28",
    },
    {
      id: "p002",
      name: "Jane Smith",
      age: 72,
      risk: 0.4,
      last_update: "2024-04-29",
    },
    {
      id: "p003",
      name: "Robert Johnson",
      age: 58,
      risk: 0.85,
      last_update: "2024-04-27",
    },
    {
      id: "p004",
      name: "Emily Davis",
      age: 81,
      risk: 0.6,
      last_update: "2024-04-29",
    },
  ];
};

const getPatientDetails = async (patientId) => {
  // This specific endpoint also doesn't seem to exist directly for fetching *all* details used in the screen.
  // The backend has /predict and /fhir/patient/{patient_id}/predict.
  // We might need to call the prediction endpoint to get risk details.
  // For now, keeping the mock logic, but ideally, this would call the prediction endpoint.
  console.warn(
    `getPatientDetails for ${patientId} called, but no direct backend endpoint defined. Using mock data.`,
  );

  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 700));

  // Mock data logic from PatientDetailScreen (simplified)
  if (patientId === "p001") {
    return {
      id: "p001",
      name: "John Doe",
      risk: 0.75,
      predictions: {
        risk: 0.75,
        top_features: ["age", "previous_admissions", "diabetes"],
        cohort_size: 120,
        shap_features: ["age", "prev_adm", "diabetes", "htn", "hf"],
        shap_values: [0.3, 0.25, 0.2, 0.15, 0.1],
      },
      explanations: { method: "SHAP", values: [0.3, 0.25, 0.2, 0.15, 0.1] },
      uncertainty: { confidence_interval: [0.65, 0.85] },
      timeline: [],
    };
  } else if (patientId === "p003") {
    return {
      id: "p003",
      name: "Robert Johnson",
      risk: 0.85,
      predictions: {
        risk: 0.85,
        top_features: ["comorbidities", "age", "lab_value_x"],
        cohort_size: 95,
        shap_features: ["comorb", "age", "lab_x", "med_y", "prev_adm"],
        shap_values: [0.4, 0.2, 0.15, 0.05, 0.05],
      },
      explanations: { method: "SHAP", values: [0.4, 0.2, 0.15, 0.05, 0.05] },
      uncertainty: { confidence_interval: [0.78, 0.92] },
      timeline: [],
    };
  }
  return {
    id: patientId,
    name: "Default Patient",
    risk: 0.55,
    predictions: {
      risk: 0.55,
      top_features: ["feature_a", "feature_b", "feature_c"],
      cohort_size: 150,
      shap_features: ["feat_a", "feat_b", "feat_c", "feat_d", "feat_e"],
      shap_values: [0.2, 0.15, 0.1, 0.05, 0.05],
    },
    explanations: { method: "SHAP", values: [0.2, 0.15, 0.1, 0.05, 0.05] },
    uncertainty: { confidence_interval: [0.45, 0.65] },
    timeline: [],
  };
};

const postPrediction = (modelName, patientData, modelVersion = null) => {
  const payload = {
    model_name: modelName,
    patient_data: patientData,
    model_version: modelVersion,
  };
  return apiClient.post("/predict", payload);
};

export default {
  getHealth,
  listModels,
  getPatients, // Still uses mock data
  getPatientDetails, // Still uses mock data
  postPrediction,
};
