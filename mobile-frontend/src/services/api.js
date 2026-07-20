import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";
import Constants from "expo-constants";

// ─── Configuration ───────────────────────────────────────────────────────
const API_BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl ||
  process.env.API_BASE_URL ||
  "http://localhost:8000";

const TOKEN_KEY = "nexora_token";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 20000,
});

apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem(TOKEN_KEY);
      if (token) config.headers.Authorization = `Bearer ${token}`;
    } catch (e) {
      // Ignore; request proceeds unauthenticated.
    }
    return config;
  },
  (error) => Promise.reject(error),
);

const extractErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(" ");
  }
  if (error?.message === "Network Error") {
    return "Can't reach the Nexora backend. Check that the API server is running and reachable from your device.";
  }
  return fallback;
};

let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status === 401) {
      await AsyncStorage.removeItem(TOKEN_KEY);
      if (onUnauthorized) onUnauthorized();
    }
    return Promise.reject(
      Object.assign(new Error(extractErrorMessage(error, "Request failed.")), {
        original: error,
        status: error?.response?.status,
      }),
    );
  },
);

export const setAuthToken = async (token) => {
  if (token) await AsyncStorage.setItem(TOKEN_KEY, token);
  else await AsyncStorage.removeItem(TOKEN_KEY);
};

export const getAuthToken = () => AsyncStorage.getItem(TOKEN_KEY);

// ─── Auth ────────────────────────────────────────────────────────────────

const register = async ({
  fullName,
  email,
  password,
  organization,
  specialty,
}) => {
  const { data } = await apiClient.post("/auth/register", {
    full_name: fullName,
    email,
    password,
    organization: organization || null,
    specialty: specialty || null,
  });
  return data;
};

const login = async ({ email, password }) => {
  const { data } = await apiClient.post("/auth/login", { email, password });
  return data;
};

const getCurrentUser = async () => {
  const { data } = await apiClient.get("/auth/me");
  return data;
};

const updateProfile = async ({ fullName, organization, specialty }) => {
  const { data } = await apiClient.patch("/auth/me", {
    full_name: fullName,
    organization,
    specialty,
  });
  return data;
};

const changePassword = async ({ currentPassword, newPassword }) => {
  const { data } = await apiClient.post("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return data;
};

const logout = async () => {
  try {
    await apiClient.post("/auth/logout");
  } catch (e) {
    // Token may already be invalid; local logout still proceeds.
  } finally {
    await setAuthToken(null);
  }
};

// ─── System ──────────────────────────────────────────────────────────────

const checkHealth = async () => {
  const { data } = await apiClient.get("/health");
  return data;
};

// ─── Models & predictions ────────────────────────────────────────────────

const getModels = async () => {
  const { data } = await apiClient.get("/models");
  const registry = data.models || {};
  return Object.entries(registry).map(([name, versions]) => {
    const latest = versions.latest || Object.values(versions)[0] || {};
    return {
      name,
      displayName: name
        .split("_")
        .map((w) => w[0].toUpperCase() + w.slice(1))
        .join(" "),
      version: latest?.config?.version || "1.0.0",
      status: "Active",
    };
  });
};

const makePrediction = async (modelName, modelVersion, patientData) => {
  const { data } = await apiClient.post("/predict", {
    model_name: modelName,
    model_version: modelVersion || undefined,
    patient_data: patientData,
  });
  return data;
};

const getPredictionFromFHIR = async (patientId, modelName, modelVersion) => {
  const { data } = await apiClient.post(
    `/fhir/patient/${patientId}/predict`,
    null,
    { params: { model_name: modelName, model_version: modelVersion } },
  );
  return data;
};

// ─── Patients ────────────────────────────────────────────────────────────

const getPatients = async ({
  search,
  riskBand,
  page = 1,
  pageSize = 200,
} = {}) => {
  const { data } = await apiClient.get("/patients", {
    params: {
      search: search || undefined,
      risk_band: riskBand && riskBand !== "all" ? riskBand : undefined,
      page,
      page_size: pageSize,
    },
  });
  return data.patients;
};

const getPatientDetails = async (patientId) => {
  const { data } = await apiClient.get(`/patients/${patientId}`);
  return data;
};

const addPatient = async (patientData) => {
  const { data } = await apiClient.post("/patients", patientData);
  return data;
};

const updatePatient = async (patientId, patientData) => {
  const { data } = await apiClient.put(`/patients/${patientId}`, patientData);
  return data;
};

const deletePatient = async (patientId) => {
  const { data } = await apiClient.delete(`/patients/${patientId}`);
  return data;
};

const recomputeRisk = async (patientId) => {
  const { data } = await apiClient.post(
    `/patients/${patientId}/recompute-risk`,
  );
  return data;
};

// ─── Dashboard ───────────────────────────────────────────────────────────

const getDashboardData = async () => {
  const { data } = await apiClient.get("/dashboard/summary");
  return data;
};

// ─── Notifications ───────────────────────────────────────────────────────

const getNotifications = async () => {
  const { data } = await apiClient.get("/notifications");
  return data;
};

const markNotificationRead = async (notificationId) => {
  const { data } = await apiClient.patch(
    `/notifications/${notificationId}/read`,
  );
  return data;
};

const markAllNotificationsRead = async () => {
  const { data } = await apiClient.post("/notifications/read-all");
  return data;
};

export default {
  setAuthToken,
  getAuthToken,
  setUnauthorizedHandler,
  register,
  login,
  getCurrentUser,
  updateProfile,
  changePassword,
  logout,
  checkHealth,
  getModels,
  makePrediction,
  getPredictionFromFHIR,
  getPatients,
  getPatientDetails,
  addPatient,
  updatePatient,
  deletePatient,
  recomputeRisk,
  getDashboardData,
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  getBaseURL: () => API_BASE_URL,
};
