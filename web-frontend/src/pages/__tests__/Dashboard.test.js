import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Dashboard from "../Dashboard";
import * as api from "../../services/api";

// Mock the API
jest.mock("../../services/api");

const mockDashboardData = {
  stats: {
    activePatients: 1284,
    highRiskPatients: 256,
    avgLengthOfStay: 4.2,
    activeModels: 5,
  },
  patientRiskDistribution: {
    highRisk: 25,
    mediumRisk: 45,
    lowRisk: 30,
  },
  admissionsData: {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    admissions: [65, 59, 80, 81, 56, 55],
    readmissions: [28, 48, 40, 19, 36, 27],
  },
  modelPerformance: {
    labels: ["Readmission", "Mortality", "LOS", "Complications"],
    scores: [0.82, 0.78, 0.75, 0.81],
  },
};

describe("Dashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getDashboardData.mockResolvedValue(mockDashboardData);
  });

  it("renders dashboard title", async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    expect(screen.getByText("Clinical Dashboard")).toBeInTheDocument();
  });

  it("displays loading state initially", () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("loads and displays dashboard data", async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("1,284")).toBeInTheDocument();
      expect(screen.getByText("256")).toBeInTheDocument();
      expect(screen.getByText("4.2 days")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });
  });

  it("displays stat cards with correct titles", async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Active Patients")).toBeInTheDocument();
      expect(screen.getByText("High Risk Patients")).toBeInTheDocument();
      expect(screen.getByText("Avg. Length of Stay")).toBeInTheDocument();
      expect(screen.getByText("Active Models")).toBeInTheDocument();
    });
  });

  it("displays chart sections", async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Admissions & Readmissions Trend"),
      ).toBeInTheDocument();
      expect(screen.getByText("Patient Risk Distribution")).toBeInTheDocument();
      expect(screen.getByText("Model Performance Metrics")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    api.getDashboardData.mockRejectedValue(new Error("API Error"));
    console.error = jest.fn(); // Suppress error logs

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(api.getDashboardData).toHaveBeenCalled();
    });

    // Should not crash, loading should stop
    await waitFor(() => {
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
  });

  it("renders generate report button", async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Generate Report")).toBeInTheDocument();
    });
  });
});
