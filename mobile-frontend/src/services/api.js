import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";

// Get API base URL from environment or use default
const API_BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl ||
  process.env.API_BASE_URL ||
  "http://localhost:8000";

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000, // 10 second timeout
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem("userToken");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.warn("Failed to retrieve auth token:", error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error(
        "API Error Response:",
        error.response.status,
        error.response.data,
      );
    } else if (error.request) {
      // Request made but no response received
      console.error("API No Response:", error.request);
    } else {
      // Error in request setup
      console.error("API Request Error:", error.message);
    }
    return Promise.reject(error);
  },
);

// API Service Functions

/**
 * Health check endpoint
 */
const getHealth = () => {
  return apiClient.get("/health");
};

/**
 * List available models
 */
const listModels = () => {
  return apiClient.get("/models");
};

/**
 * Get list of patients
 * Note: This endpoint may not exist in the code yet.
 * Falls back to mock data if the request fails.
 */
const getPatients = async () => {
  try {
    // Try to fetch from code first
    const response = await apiClient.get("/patients");
    return response.data;
  } catch (error) {
    console.warn(
      "Failed to fetch patients from code, using mock data:",
      error.message,
    );
    // Fallback to mock data
    return getMockPatients();
  }
};

/**
 * Get patient details including predictions
 */
const getPatientDetails = async (patientId) => {
  try {
    // Try to fetch from code first
    const response = await apiClient.get(`/patients/${patientId}`);
    return response.data;
  } catch (error) {
    console.warn(
      `Failed to fetch patient ${patientId} from code, using mock data:`,
      error.message,
    );
    // Fallback to mock data
    return getMockPatientDetails(patientId);
  }
};

/**
 * Submit prediction request
 */
const postPrediction = async (modelName, patientData, modelVersion = null) => {
  const payload = {
    model_name: modelName,
    patient_data: patientData,
    model_version: modelVersion,
  };
  const response = await apiClient.post("/predict", payload);
  return response.data;
};

/**
 * Get prediction using FHIR patient ID
 */
const getPredictionFromFHIR = async (
  patientId,
  modelName,
  modelVersion = null,
) => {
  const params = {
    model_name: modelName,
    ...(modelVersion && { model_version: modelVersion }),
  };
  const response = await apiClient.post(
    `/fhir/patient/${patientId}/predict`,
    null,
    {
      params,
    },
  );
  return response.data;
};

/**
 * Login user (mock implementation - replace with real auth endpoint)
 */
const login = async (username, password) => {
  try {
    // Try real code authentication first
    const response = await apiClient.post("/auth/login", {
      username,
      password,
    });
    return response.data;
  } catch (error) {
    console.warn("code auth not available, using mock authentication");
    // Fallback to mock authentication for development
    if (username === "clinician" && password === "password123") {
      return {
        success: true,
        token: "mock-token-" + Date.now(),
        username: username,
      };
    }
    throw new Error("Invalid credentials");
  }
};

/**
 * Logout user
 */
const logout = async () => {
  try {
    await apiClient.post("/auth/logout");
  } catch (error) {
    console.warn(
      "code logout failed, clearing local session:",
      error.message,
    );
  }
  // Always clear local storage
  await AsyncStorage.multiRemove(["userToken", "username"]);
};

// Mock Data Functions (Fallback when code is unavailable)

const getMockPatients = () => {
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
    {
      id: "p005",
      name: "Michael Brown",
      age: 55,
      risk: 0.25,
      last_update: "2024-04-30",
    },
    {
      id: "p006",
      name: "Sarah Wilson",
      age: 68,
      risk: 0.9,
      last_update: "2024-04-26",
    },
    {
      id: "p007",
      name: "David Lee",
      age: 75,
      risk: 0.55,
      last_update: "2024-04-30",
    },
    {
      id: "p008",
      name: "Laura Martinez",
      age: 62,
      risk: 0.3,
      last_update: "2024-04-28",
    },
  ];
};

const getMockPatientDetails = (patientId) => {
  const mockDetails = {
    p001: {
      id: "p001",
      name: "John Doe",
      age: 65,
      risk: 0.75,
      predictions: {
        risk: 0.75,
        top_features: [
          "age > 60",
          "previous_admissions > 2",
          "diabetes diagnosis",
        ],
        cohort_size: 120,
        shap_features: ["Age", "Prev Adm", "Diabetes", "HTN", "HF"],
        shap_values: [0.3, 0.25, 0.2, 0.15, 0.1],
      },
      explanations: { method: "SHAP", values: [0.3, 0.25, 0.2, 0.15, 0.1] },
      uncertainty: { confidence_interval: [0.65, 0.85] },
      timeline: [
        { event: "Admission", date: "2024-04-10" },
        { event: "Lab Test (High Glucose)", date: "2024-04-11" },
        { event: "Diagnosis: HF", date: "2024-04-12" },
        { event: "Discharge", date: "2024-04-18" },
      ],
    },
    p003: {
      id: "p003",
      name: "Robert Johnson",
      age: 58,
      risk: 0.85,
      predictions: {
        risk: 0.85,
        top_features: [
          "multiple comorbidities",
          "age > 55",
          "lab_value_x abnormal",
        ],
        cohort_size: 95,
        shap_features: ["Comorb", "Age", "Lab X", "Med Y", "Prev Adm"],
        shap_values: [0.4, 0.2, 0.15, 0.05, 0.05],
      },
      explanations: { method: "SHAP", values: [0.4, 0.2, 0.15, 0.05, 0.05] },
      uncertainty: { confidence_interval: [0.78, 0.92] },
      timeline: [
        { event: "Admission", date: "2024-04-05" },
        { event: "Surgery", date: "2024-04-07" },
        { event: "ICU Stay", date: "2024-04-08" },
        { event: "Discharge", date: "2024-04-20" },
      ],
    },
  };

  return (
    mockDetails[patientId] || {
      id: patientId,
      name: "Default Patient",
      age: 70,
      risk: 0.55,
      predictions: {
        risk: 0.55,
        top_features: ["feature_a", "feature_b", "feature_c"],
        cohort_size: 150,
        shap_features: ["Feat A", "Feat B", "Feat C", "Feat D", "Feat E"],
        shap_values: [0.2, 0.15, 0.1, 0.05, 0.05],
      },
      explanations: { method: "SHAP", values: [0.2, 0.15, 0.1, 0.05, 0.05] },
      uncertainty: { confidence_interval: [0.45, 0.65] },
      timeline: [],
    }
  );
};

export default {
  getHealth,
  listModels,
  getPatients,
  getPatientDetails,
  postPrediction,
  getPredictionFromFHIR,
  login,
  logout,
  // Expose base URL for debugging
  getBaseURL: () => API_BASE_URL,
};
