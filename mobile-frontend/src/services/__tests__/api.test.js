import axios from "axios";
import apiService from "../api";

// Mock axios
jest.mock("axios");

// Mock AsyncStorage
jest.mock("@react-native-async-storage/async-storage", () => ({
  getItem: jest.fn(() => Promise.resolve("mock-token")),
  setItem: jest.fn(() => Promise.resolve()),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

describe("API Service", () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };

  beforeAll(() => {
    axios.create.mockReturnValue(mockAxiosInstance);
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getHealth", () => {
    it("should fetch health status", async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { status: "healthy" },
      });

      const result = await apiService.getHealth();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/health");
      expect(result.data.status).toBe("healthy");
    });
  });

  describe("listModels", () => {
    it("should fetch available models", async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { models: ["model1", "model2"] },
      });

      const result = await apiService.listModels();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/models");
      expect(result.data.models).toHaveLength(2);
    });
  });

  describe("getPatients", () => {
    it("should fetch patients from code", async () => {
      const mockPatients = [{ id: "p001", name: "John Doe" }];
      mockAxiosInstance.get.mockResolvedValue({ data: mockPatients });

      const result = await apiService.getPatients();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/patients");
      expect(result).toEqual(mockPatients);
    });

    it("should fallback to mock data on error", async () => {
      mockAxiosInstance.get.mockRejectedValue(new Error("Network error"));

      const result = await apiService.getPatients();
      expect(result).toBeInstanceOf(Array);
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe("getPatientDetails", () => {
    it("should fetch patient details from code", async () => {
      const mockDetails = {
        id: "p001",
        name: "John Doe",
        risk: 0.75,
      };
      mockAxiosInstance.get.mockResolvedValue({ data: mockDetails });

      const result = await apiService.getPatientDetails("p001");
      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/patients/p001");
      expect(result.id).toBe("p001");
    });

    it("should fallback to mock data on error", async () => {
      mockAxiosInstance.get.mockRejectedValue(new Error("Network error"));

      const result = await apiService.getPatientDetails("p001");
      expect(result).toHaveProperty("id");
      expect(result).toHaveProperty("risk");
    });
  });

  describe("postPrediction", () => {
    it("should submit prediction request", async () => {
      const mockResponse = { predictions: { risk: 0.75 } };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const patientData = { demographics: {}, clinical_events: [] };
      const result = await apiService.postPrediction(
        "model1",
        patientData,
        "v1.0",
      );

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/predict", {
        model_name: "model1",
        patient_data: patientData,
        model_version: "v1.0",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("login", () => {
    it("should authenticate with code", async () => {
      const mockResponse = {
        success: true,
        token: "test-token",
        username: "clinician",
      };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiService.login("clinician", "password");

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/auth/login", {
        username: "clinician",
        password: "password",
      });
      expect(result.success).toBe(true);
    });

    it("should fallback to mock auth on error", async () => {
      mockAxiosInstance.post.mockRejectedValue(new Error("code unavailable"));

      const result = await apiService.login("clinician", "password123");
      expect(result.success).toBe(true);
      expect(result.token).toBeTruthy();
    });

    it("should reject invalid credentials in mock mode", async () => {
      mockAxiosInstance.post.mockRejectedValue(new Error("code unavailable"));

      await expect(apiService.login("invalid", "invalid")).rejects.toThrow(
        "Invalid credentials",
      );
    });
  });

  describe("logout", () => {
    it("should call code logout endpoint", async () => {
      mockAxiosInstance.post.mockResolvedValue({});

      await apiService.logout();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith("/auth/logout");
    });
  });
});
