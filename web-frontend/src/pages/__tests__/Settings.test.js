import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Settings from "../Settings";
import * as api from "../../services/api";

jest.mock("../../services/api");

describe("Settings", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.checkHealth.mockResolvedValue({
      status: "healthy",
      timestamp: new Date().toISOString(),
    });
  });

  it("renders settings title", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("displays all settings tabs", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    expect(screen.getByText("User Profile")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Notifications")).toBeInTheDocument();
    expect(screen.getByText("Data Management")).toBeInTheDocument();
    expect(screen.getByText("System")).toBeInTheDocument();
  });

  it("shows user profile fields by default", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    expect(screen.getByDisplayValue("John")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Doe")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("john.doe@hospital.org"),
    ).toBeInTheDocument();
  });

  it("switches to security tab", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    fireEvent.click(screen.getByText("Security"));

    expect(screen.getByText("Security Settings")).toBeInTheDocument();
    expect(screen.getByText("Two-Factor Authentication")).toBeInTheDocument();
  });

  it("switches to notifications tab", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    fireEvent.click(screen.getByText("Notifications"));

    expect(screen.getByText("Notification Preferences")).toBeInTheDocument();
    expect(screen.getByText("High-Risk Patient Alerts")).toBeInTheDocument();
  });

  it("switches to data management tab", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    fireEvent.click(screen.getByText("Data Management"));

    expect(screen.getByText("Data Management")).toBeInTheDocument();
    expect(screen.getByText("Data Sources")).toBeInTheDocument();
  });

  it("switches to system tab", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    fireEvent.click(screen.getByText("System"));

    expect(screen.getByText("System Settings")).toBeInTheDocument();
    expect(screen.getByText("System Information")).toBeInTheDocument();
  });

  it("displays save button", () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    expect(screen.getByText("Save Settings")).toBeInTheDocument();
  });

  it("shows success message on save", async () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    fireEvent.click(screen.getByText("Save Settings"));

    await waitFor(() => {
      expect(
        screen.getByText("Settings saved successfully"),
      ).toBeInTheDocument();
    });
  });

  it("performs health check", async () => {
    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    // Switch to system tab
    fireEvent.click(screen.getByText("System"));

    const checkHealthButton = screen.getByText("Check Health");
    fireEvent.click(checkHealthButton);

    await waitFor(() => {
      expect(api.checkHealth).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/System is healthy/)).toBeInTheDocument();
    });
  });

  it("handles health check errors", async () => {
    api.checkHealth.mockRejectedValue(new Error("Health check failed"));
    console.error = jest.fn();

    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>,
    );

    fireEvent.click(screen.getByText("System"));
    fireEvent.click(screen.getByText("Check Health"));

    await waitFor(() => {
      expect(screen.getByText(/health check failed/i)).toBeInTheDocument();
    });
  });
});
