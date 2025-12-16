import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import PatientDetail from "../PatientDetail";
import * as api from "../../services/api";

jest.mock("../../services/api");

const mockPatient = {
  id: "P00001",
  name: "John Smith",
  age: 58,
  dob: "1967-05-12",
  gender: "Male",
  primaryDiagnosis: "Type 2 Diabetes",
  riskScore: 0.72,
  phone: "(555) 123-4567",
  email: "john.smith@example.com",
  address: "123 Main St, Anytown, CA 94123",
  labResults: [
    { date: "2025-01-15", glucose: 142, hemoglobin: 13.2 },
    { date: "2025-02-01", glucose: 156, hemoglobin: 12.9 },
  ],
  diagnoses: [{ name: "Type 2 Diabetes", date: "2020-03-15", code: "E11.9" }],
  riskFactors: [{ name: "Previous Hospitalizations", impact: 0.28 }],
  interventions: [
    {
      name: "Medication Adherence Program",
      description: "Enroll in monitoring program",
      priority: "High",
    },
  ],
  medications: [
    { name: "Metformin", dosage: "1000mg", frequency: "Twice daily" },
  ],
  timeline: [
    {
      title: "Initial Diagnosis",
      date: "2020-03-15",
      description: "Diagnosed with Type 2 Diabetes",
    },
  ],
};

describe("PatientDetail", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getPatientDetail.mockResolvedValue(mockPatient);
  });

  const renderWithRouter = () => {
    return render(
      <BrowserRouter>
        <Routes>
          <Route path="/patients/:id" element={<PatientDetail />} />
        </Routes>
      </BrowserRouter>,
      { initialEntries: ["/patients/P00001"] },
    );
  };

  it("displays loading state initially", () => {
    renderWithRouter();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("loads and displays patient data", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
      expect(screen.getByText("ID: P00001")).toBeInTheDocument();
    });
  });

  it("displays patient demographics", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText(/58 years/)).toBeInTheDocument();
      expect(screen.getByText("Male")).toBeInTheDocument();
      expect(screen.getByText("Type 2 Diabetes")).toBeInTheDocument();
    });
  });

  it("displays contact information", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText("(555) 123-4567")).toBeInTheDocument();
      expect(screen.getByText("john.smith@example.com")).toBeInTheDocument();
    });
  });

  it("displays tabs for different sections", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText("Clinical Data")).toBeInTheDocument();
      expect(screen.getByText("Risk Analysis")).toBeInTheDocument();
      expect(screen.getByText("Medications")).toBeInTheDocument();
      expect(screen.getByText("Timeline")).toBeInTheDocument();
    });
  });

  it("displays back button", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText("Back")).toBeInTheDocument();
    });
  });

  it("displays action buttons", async () => {
    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText("Download Records")).toBeInTheDocument();
      expect(screen.getByText("Schedule Follow-up")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    api.getPatientDetail.mockRejectedValue(new Error("API Error"));
    console.error = jest.fn();

    renderWithRouter();

    await waitFor(() => {
      expect(api.getPatientDetail).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
  });
});
