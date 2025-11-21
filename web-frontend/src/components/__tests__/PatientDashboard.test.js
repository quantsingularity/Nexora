import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PatientDashboard } from "../PatientDashboard";
import { PatientContext } from "../../contexts/PatientContext";
import { mockPatientData, mockPredictions } from "../../__mocks__/mockData";

// Mock the API calls
jest.mock("../../services/api", () => ({
  getPatientData: jest.fn(() => Promise.resolve(mockPatientData)),
  getPredictions: jest.fn(() => Promise.resolve(mockPredictions)),
}));

describe("PatientDashboard", () => {
  const mockSetSelectedPatient = jest.fn();

  const renderWithContext = (component) => {
    return render(
      <PatientContext.Provider
        value={{
          selectedPatient: null,
          setSelectedPatient: mockSetSelectedPatient,
        }}
      >
        {component}
      </PatientContext.Provider>,
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading state initially", () => {
    renderWithContext(<PatientDashboard />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("loads and displays patient data", async () => {
    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      expect(screen.getByText(mockPatientData.name)).toBeInTheDocument();
      expect(
        screen.getByText(`Age: ${mockPatientData.age}`),
      ).toBeInTheDocument();
    });
  });

  it("displays risk predictions", async () => {
    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/risk score/i)).toBeInTheDocument();
      expect(
        screen.getByText(`${mockPredictions.risk * 100}%`),
      ).toBeInTheDocument();
    });
  });

  it("displays feature importance chart", async () => {
    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      expect(
        screen.getByTestId("feature-importance-chart"),
      ).toBeInTheDocument();
    });
  });

  it("handles patient selection", async () => {
    renderWithContext(<PatientDashboard />);

    const patientSelect = screen.getByLabelText(/select patient/i);
    await userEvent.selectOptions(patientSelect, "12345");

    expect(mockSetSelectedPatient).toHaveBeenCalledWith("12345");
  });

  it("displays error state when API fails", async () => {
    const mockError = new Error("API Error");
    jest.spyOn(console, "error").mockImplementation(() => {});
    require("../../services/api").getPatientData.mockRejectedValueOnce(
      mockError,
    );

    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText(/error loading patient data/i),
      ).toBeInTheDocument();
    });
  });

  it("updates predictions when patient changes", async () => {
    renderWithContext(<PatientDashboard />);

    // Initial load
    await waitFor(() => {
      expect(
        screen.getByText(`${mockPredictions.risk * 100}%`),
      ).toBeInTheDocument();
    });

    // Change patient
    const patientSelect = screen.getByLabelText(/select patient/i);
    await userEvent.selectOptions(patientSelect, "67890");

    // Verify new predictions loaded
    await waitFor(() => {
      expect(screen.getByText(/loading predictions/i)).toBeInTheDocument();
    });
  });

  it("displays patient demographics correctly", async () => {
    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/demographics/i)).toBeInTheDocument();
      expect(
        screen.getByText(`Gender: ${mockPatientData.gender}`),
      ).toBeInTheDocument();
      expect(
        screen.getByText(`Insurance: ${mockPatientData.insurance}`),
      ).toBeInTheDocument();
    });
  });

  it("displays clinical history", async () => {
    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/clinical history/i)).toBeInTheDocument();
      mockPatientData.diagnoses.forEach((diagnosis) => {
        expect(screen.getByText(diagnosis)).toBeInTheDocument();
      });
    });
  });

  it("handles prediction explanation toggle", async () => {
    renderWithContext(<PatientDashboard />);

    await waitFor(() => {
      const toggleButton = screen.getByText(/show explanation/i);
      fireEvent.click(toggleButton);
      expect(screen.getByText(/feature importance/i)).toBeInTheDocument();
    });
  });
});
