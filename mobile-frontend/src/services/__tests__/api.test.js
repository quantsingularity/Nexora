import apiService from "../api";

// Mock AsyncStorage
const mockAsyncStorage = {
  getItem: jest.fn(() => Promise.resolve("mock-token")),
  setItem: jest.fn(() => Promise.resolve()),
  multiRemove: jest.fn(() => Promise.resolve()),
};

jest.mock("@react-native-async-storage/async-storage", () => mockAsyncStorage);

describe("API Service", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getBaseURL", () => {
    it("should return API base URL", () => {
      const baseURL = apiService.getBaseURL();
      expect(baseURL).toBeDefined();
      expect(typeof baseURL).toBe("string");
    });
  });

  describe("getHealth", () => {
    it("should return a promise", () => {
      const result = apiService.getHealth();
      expect(result).toBeInstanceOf(Promise);
    });
  });

  describe("listModels", () => {
    it("should return a promise", () => {
      const result = apiService.listModels();
      expect(result).toBeInstanceOf(Promise);
    });
  });

  describe("getPatients", () => {
    it("should return a promise", async () => {
      const result = apiService.getPatients();
      expect(result).toBeInstanceOf(Promise);
    });

    it("should return array of patients (mock fallback)", async () => {
      // Since code is not running, it should fallback to mock data
      const result = await apiService.getPatients();
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toHaveProperty("id");
      expect(result[0]).toHaveProperty("name");
      expect(result[0]).toHaveProperty("risk");
    });
  });

  describe("getPatientDetails", () => {
    it("should return a promise", () => {
      const result = apiService.getPatientDetails("p001");
      expect(result).toBeInstanceOf(Promise);
    });

    it("should return patient details (mock fallback)", async () => {
      const result = await apiService.getPatientDetails("p001");
      expect(result).toHaveProperty("id");
      expect(result).toHaveProperty("name");
      expect(result).toHaveProperty("risk");
      expect(result).toHaveProperty("predictions");
      expect(result).toHaveProperty("uncertainty");
    });
  });

  describe("postPrediction", () => {
    it("should return a promise", () => {
      const patientData = {
        patient_id: "p001",
        demographics: {},
        clinical_events: [],
      };
      const result = apiService.postPrediction("model1", patientData);
      expect(result).toBeInstanceOf(Promise);
    });
  });

  describe("login", () => {
    it("should authenticate with valid credentials (mock)", async () => {
      const result = await apiService.login("clinician", "password123");
      expect(result.success).toBe(true);
      expect(result.token).toBeTruthy();
      expect(result.username).toBe("clinician");
    });

    it("should reject invalid credentials", async () => {
      await expect(apiService.login("invalid", "invalid")).rejects.toThrow(
        "Invalid credentials",
      );
    });
  });

  describe("logout", () => {
    it("should clear local storage", async () => {
      await apiService.logout();
      expect(mockAsyncStorage.multiRemove).toHaveBeenCalledWith([
        "userToken",
        "username",
      ]);
    });
  });

  describe("getPredictionFromFHIR", () => {
    it("should return a promise", () => {
      const result = apiService.getPredictionFromFHIR("p001", "model1");
      expect(result).toBeInstanceOf(Promise);
    });
  });
});
