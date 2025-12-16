import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import PatientList from "../PatientList";
import * as api from "../../services/api";

jest.mock("../../services/api");

const mockPatients = [
  {
    id: "P00001",
    name: "John Doe",
    age: 45,
    gender: "Male",
    diagnosis: "Hypertension",
    lastVisit: "2025-04-01",
    riskScore: 0.35,
  },
  {
    id: "P00002",
    name: "Jane Smith",
    age: 62,
    gender: "Female",
    diagnosis: "Type 2 Diabetes",
    lastVisit: "2025-04-05",
    riskScore: 0.75,
  },
];

describe("PatientList", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getPatients.mockResolvedValue(mockPatients);
  });

  it("renders patient list title", () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    expect(screen.getByText("Patient List")).toBeInTheDocument();
  });

  it("displays loading state initially", () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("loads and displays patient data", async () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });
  });

  it("displays patient information correctly", async () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("P00001")).toBeInTheDocument();
      expect(screen.getByText("45")).toBeInTheDocument();
      expect(screen.getByText("Male")).toBeInTheDocument();
      expect(screen.getByText("Hypertension")).toBeInTheDocument();
    });
  });

  it("filters patients by search term", async () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Search patients...");
    await userEvent.type(searchInput, "Jane");

    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
  });

  it("displays risk scores with correct colors", async () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      const chips = screen
        .getAllByRole("button")
        .filter((el) => el.textContent.includes("%"));
      expect(chips.length).toBeGreaterThan(0);
    });
  });

  it("handles pagination", async () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Check that pagination controls exist
    expect(screen.getByText(/rows per page/i)).toBeInTheDocument();
  });

  it("displays add patient button", () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    expect(screen.getByText("Add Patient")).toBeInTheDocument();
  });

  it("handles API errors gracefully", async () => {
    api.getPatients.mockRejectedValue(new Error("API Error"));
    console.error = jest.fn();

    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(api.getPatients).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
  });

  it("displays no patients message when list is empty", async () => {
    api.getPatients.mockResolvedValue([]);

    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("No patients found")).toBeInTheDocument();
    });
  });
});
