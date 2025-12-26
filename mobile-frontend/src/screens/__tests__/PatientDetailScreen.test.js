import React from "react";
import { render, waitFor } from "@testing-library/react-native";
import PatientDetailScreen from "../PatientDetailScreen";
import apiService from "../../services/api";
import { mockPatientDetails } from "../../__mocks__/mockData";

// Mock dependencies
jest.mock("../../services/api");

const mockRoute = {
  params: {
    patientId: "p001",
    patientName: "John Doe",
  },
};

const mockNavigation = {
  setOptions: jest.fn(),
  navigate: jest.fn(),
};

describe("PatientDetailScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.getPatientDetails.mockResolvedValue(mockPatientDetails);
  });

  it("renders correctly", async () => {
    const { getByTestId } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(
      () => {
        expect(getByTestId("patient-details")).toBeTruthy();
      },
      { timeout: 3000 },
    );
  }, 10000);

  it("displays patient risk score", async () => {
    const { getByTestId } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      const riskScore = getByTestId("risk-score");
      expect(riskScore).toBeTruthy();
      expect(riskScore.props.children).toContain("75%");
    });
  });

  it("displays patient name", async () => {
    const { getByTestId } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      const patientName = getByTestId("patient-name");
      expect(patientName).toBeTruthy();
      expect(patientName.props.children).toBe("John Doe");
    });
  });

  it("displays risk chart", async () => {
    const { getByTestId } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByTestId("risk-chart")).toBeTruthy();
    });
  });

  it("displays clinical history", async () => {
    const { getByTestId } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(
      () => {
        expect(getByTestId("clinical-history-list")).toBeTruthy();
      },
      { timeout: 3000 },
    );
  }, 10000);

  it("displays error message on API failure", async () => {
    apiService.getPatientDetails.mockRejectedValue(new Error("Network error"));

    const { getByTestId } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByTestId("error-message")).toBeTruthy();
    });
  });

  it("sets navigation title", async () => {
    render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(mockNavigation.setOptions).toHaveBeenCalledWith({
        title: "John Doe",
      });
    });
  });

  it("displays timeline events", async () => {
    const { getByText } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByText("Admission")).toBeTruthy();
      expect(getByText("Lab Test (High Glucose)")).toBeTruthy();
    });
  });

  it("displays SHAP feature importance", async () => {
    const { getByText } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByText(/Risk Factor Importance/)).toBeTruthy();
    });
  });

  it("displays confidence interval", async () => {
    const { getByText } = render(
      <PatientDetailScreen route={mockRoute} navigation={mockNavigation} />,
    );

    await waitFor(() => {
      expect(getByText(/Confidence:/)).toBeTruthy();
      expect(getByText(/65%/)).toBeTruthy();
      expect(getByText(/85%/)).toBeTruthy();
    });
  });
});
