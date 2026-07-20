import axios from "axios";

// ─── Configuration ───────────────────────────────────────────────────────────
// Base URL of the FastAPI backend (code/backend). Configure per-environment
// via REACT_APP_API_BASE_URL (see .env.example).
const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";
const API_TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT || "30000", 10);
const TOKEN_KEY = "nexora_token";

// ─── Axios instance ──────────────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error),
);

// Normalize FastAPI error payloads ({"detail": "..."} or validation arrays)
// into a single human-readable message.
const extractErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(" ");
  }
  if (error?.message === "Network Error" || error?.code === "ERR_NETWORK") {
    return "Can't reach the Nexora backend. Make sure the API server is running.";
  }
  return fallback;
};

let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
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

export const setAuthToken = (token) => {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
};

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY);

// ─── Auth ─────────────────────────────────────────────────────────────────

export const register = async ({
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

export const login = async ({ email, password }) => {
  const { data } = await apiClient.post("/auth/login", { email, password });
  return data;
};

export const getCurrentUser = async () => {
  const { data } = await apiClient.get("/auth/me");
  return data;
};

export const updateProfile = async ({ fullName, organization, specialty }) => {
  const { data } = await apiClient.patch("/auth/me", {
    full_name: fullName,
    organization,
    specialty,
  });
  return data;
};

export const changePassword = async ({ currentPassword, newPassword }) => {
  const { data } = await apiClient.post("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return data;
};

export const logout = async () => {
  try {
    await apiClient.post("/auth/logout");
  } catch (e) {
    // Token may already be invalid/expired; logging out locally still succeeds.
  } finally {
    setAuthToken(null);
  }
};

// ─── System ───────────────────────────────────────────────────────────────

export const checkHealth = async () => {
  const { data } = await apiClient.get("/health");
  return data;
};

// ─── Models ───────────────────────────────────────────────────────────────

export const getModels = async () => {
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
      path: latest?.path,
    };
  });
};

export const makePrediction = async (modelName, modelVersion, patientData) => {
  const { data } = await apiClient.post("/predict", {
    model_name: modelName,
    model_version: modelVersion || undefined,
    patient_data: patientData,
  });
  return data;
};

export const getPredictionFromFHIR = async (
  patientId,
  modelName,
  modelVersion,
) => {
  const { data } = await apiClient.post(
    `/fhir/patient/${patientId}/predict`,
    null,
    { params: { model_name: modelName, model_version: modelVersion } },
  );
  return data;
};

// ─── Patients ─────────────────────────────────────────────────────────────

export const getPatients = async ({
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

export const getPatientDetail = async (patientId) => {
  const { data } = await apiClient.get(`/patients/${patientId}`);
  return data;
};

export const addPatient = async (patientData) => {
  const { data } = await apiClient.post("/patients", patientData);
  return data;
};

export const updatePatient = async (patientId, patientData) => {
  const { data } = await apiClient.put(`/patients/${patientId}`, patientData);
  return data;
};

export const deletePatient = async (patientId) => {
  const { data } = await apiClient.delete(`/patients/${patientId}`);
  return data;
};

export const recomputeRisk = async (patientId) => {
  const { data } = await apiClient.post(
    `/patients/${patientId}/recompute-risk`,
  );
  return data;
};

// ─── Dashboard ────────────────────────────────────────────────────────────

export const getDashboardData = async () => {
  const { data } = await apiClient.get("/dashboard/summary");
  return data;
};

// ─── Notifications ────────────────────────────────────────────────────────

export const getNotifications = async () => {
  const { data } = await apiClient.get("/notifications");
  return data;
};

export const markNotificationRead = async (notificationId) => {
  const { data } = await apiClient.patch(
    `/notifications/${notificationId}/read`,
  );
  return data;
};

export const markAllNotificationsRead = async () => {
  const { data } = await apiClient.post("/notifications/read-all");
  return data;
};

// ─── Default export ──────────────────────────────────────────────────────

const api = {
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
  getPatientDetail,
  addPatient,
  updatePatient,
  deletePatient,
  recomputeRisk,
  getDashboardData,
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
};

export default api;
