import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import PredictionModels from "../PredictionModels";
import * as api from "../../services/api";

jest.mock("../../services/api");

const mockModels = [
  {
    name: "Readmission Risk Predictor",
    version: "1.2.0",
    lastUpdated: "2025-03-15",
    status: "Active",
  },
  {
    name: "Mortality Prediction Model",
    version: "1.0.5",
    lastUpdated: "2025-02-28",
    status: "Active",
  },
];

describe("PredictionModels", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getModels.mockResolvedValue(mockModels);
  });

  it("renders prediction models title", () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    expect(screen.getByText("Prediction Models")).toBeInTheDocument();
  });

  it("displays loading state initially", () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("loads and displays model data", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Readmission Risk Predictor"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Mortality Prediction Model"),
      ).toBeInTheDocument();
    });
  });

  it("displays model information correctly", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Version: 1.2.0/)).toBeInTheDocument();
      expect(screen.getByText(/Updated: 2025-03-15/)).toBeInTheDocument();
    });
  });

  it("displays Available Models section", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Available Models")).toBeInTheDocument();
    });
  });

  it("displays model tabs", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Performance")).toBeInTheDocument();
      expect(screen.getByText("Training History")).toBeInTheDocument();
      expect(screen.getByText("Configuration")).toBeInTheDocument();
    });
  });

  it("displays deploy new model button", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Deploy New Model")).toBeInTheDocument();
    });
  });

  it("displays model action buttons", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Export Model")).toBeInTheDocument();
      expect(screen.getByText("Retrain Model")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    api.getModels.mockRejectedValue(new Error("API Error"));
    console.error = jest.fn();

    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(api.getModels).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
  });

  it("shows model status badges", async () => {
    render(
      <BrowserRouter>
        <PredictionModels />
      </BrowserRouter>,
    );

    await waitFor(() => {
      const activeChips = screen.getAllByText("Active");
      expect(activeChips.length).toBeGreaterThan(0);
    });
  });
});
