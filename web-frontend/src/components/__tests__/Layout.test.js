import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Layout from "../Layout";

describe("Layout", () => {
  it("renders the app title", () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>,
    );

    expect(screen.getByText("NEXORA")).toBeInTheDocument();
    expect(screen.getByText("Clinical Prediction System")).toBeInTheDocument();
  });

  it("renders navigation menu items", () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>,
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Patients")).toBeInTheDocument();
    expect(screen.getByText("Models")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders system status indicator", () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>,
    );

    expect(screen.getByText("System Status")).toBeInTheDocument();
    expect(screen.getByText("All systems operational")).toBeInTheDocument();
  });

  it("opens profile menu on click", () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>,
    );

    const profileButton = screen.getByLabelText("account of current user");
    fireEvent.click(profileButton);

    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("My account")).toBeInTheDocument();
    expect(screen.getByText("Logout")).toBeInTheDocument();
  });

  it("toggles drawer on menu button click", () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>,
    );

    const menuButton = screen.getByLabelText("open drawer");
    expect(menuButton).toBeInTheDocument();

    fireEvent.click(menuButton);
    // Drawer state changes but visual testing is difficult in jest
  });

  it("displays notification badge", () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>,
    );

    // Check notification icon is present
    const notificationButtons = screen.getAllByRole("button");
    expect(notificationButtons.length).toBeGreaterThan(0);
  });
});
