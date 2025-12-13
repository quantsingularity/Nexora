import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import HomeScreen from "../HomeScreen";
import apiService from "../../services/api";
import { mockPatients } from "../../__mocks__/mockData";

// Mock dependencies
jest.mock("../../services/api");
jest.mock("@react-native-async-storage/async-storage", () => ({
  setItem: jest.fn(() => Promise.resolve()),
  getItem: jest.fn(() => Promise.resolve("TestUser")),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

const mockNavigation = {
  replace: jest.fn(),
  navigate: jest.fn(),
};

describe("HomeScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.getPatients.mockResolvedValue(mockPatients);
  });

  it("renders correctly", async () => {
    const { getByTestId, getByText } = render(
      <HomeScreen navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByTestId("patient-list-tab")).toBeTruthy();
      expect(getByText(/Welcome/)).toBeTruthy();
    });
  });

  it("loads and displays patients", async () => {
    const { getByText } = render(<HomeScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText("John Doe")).toBeTruthy();
      expect(getByText("Jane Smith")).toBeTruthy();
    });
  });

  it("filters patients by search term", async () => {
    const { getByTestId, getByText, queryByText } = render(
      <HomeScreen navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByText("John Doe")).toBeTruthy();
    });

    const searchInput = getByTestId("search-input");
    fireEvent.changeText(searchInput, "John");

    await waitFor(() => {
      expect(getByText("John Doe")).toBeTruthy();
      expect(queryByText("Jane Smith")).toBeNull();
    });
  });

  it("navigates to patient detail on patient press", async () => {
    const { getByTestId, getByText } = render(
      <HomeScreen navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByText("John Doe")).toBeTruthy();
    });

    fireEvent.press(getByTestId("patient-item-p001"));

    expect(mockNavigation.navigate).toHaveBeenCalledWith("PatientDetail", {
      patientId: "p001",
      patientName: "John Doe",
    });
  });

  it("handles logout", async () => {
    apiService.logout.mockResolvedValue();

    const { getByText } = render(<HomeScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText("Logout")).toBeTruthy();
    });

    fireEvent.press(getByText("Logout"));

    await waitFor(() => {
      expect(apiService.logout).toHaveBeenCalled();
      expect(mockNavigation.replace).toHaveBeenCalledWith("Login");
    });
  });

  it("displays error message on API failure", async () => {
    apiService.getPatients.mockRejectedValue(new Error("Network error"));

    const { getByTestId } = render(<HomeScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByTestId("error-message")).toBeTruthy();
      expect(getByTestId("retry-button")).toBeTruthy();
    });
  });

  it("retries loading on retry button press", async () => {
    apiService.getPatients
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(mockPatients);

    const { getByTestId, getByText } = render(
      <HomeScreen navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByTestId("error-message")).toBeTruthy();
    });

    fireEvent.press(getByTestId("retry-button"));

    await waitFor(() => {
      expect(getByText("John Doe")).toBeTruthy();
    });
  });

  it("handles pull to refresh", async () => {
    const { getByTestId } = render(<HomeScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(apiService.getPatients).toHaveBeenCalledTimes(1);
    });

    const patientList = getByTestId("patient-list");
    fireEvent(patientList, "refresh");

    await waitFor(() => {
      expect(apiService.getPatients).toHaveBeenCalledTimes(2);
    });
  });
});
