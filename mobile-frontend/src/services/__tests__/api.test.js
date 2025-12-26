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

  describe("getPatients", () => {
    it("should return array of patients (mock fallback)", async () => {
      // Since backend is not running, it should fallback to mock data
      const result = await apiService.getPatients();
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toHaveProperty("id");
      expect(result[0]).toHaveProperty("name");
      expect(result[0]).toHaveProperty("risk");
    });
  });

  describe("getPatientDetails", () => {
    it("should return patient details (mock fallback)", async () => {
      const result = await apiService.getPatientDetails("p001");
      expect(result).toHaveProperty("id");
      expect(result).toHaveProperty("name");
      expect(result).toHaveProperty("risk");
      expect(result).toHaveProperty("predictions");
      expect(result).toHaveProperty("uncertainty");
    });

    it("should return default patient for unknown ID", async () => {
      const result = await apiService.getPatientDetails("unknown");
      expect(result).toHaveProperty("id");
      expect(result.id).toBe("unknown");
      expect(result).toHaveProperty("name");
      expect(result).toHaveProperty("predictions");
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
});
