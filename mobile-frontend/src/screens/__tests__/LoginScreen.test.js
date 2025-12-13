import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import LoginScreen from "../LoginScreen";
import apiService from "../../services/api";

// Mock dependencies
jest.mock("../../services/api");
jest.mock("@react-native-async-storage/async-storage", () => ({
  setItem: jest.fn(() => Promise.resolve()),
  getItem: jest.fn(() => Promise.resolve(null)),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

jest.spyOn(Alert, "alert");

const mockNavigation = {
  replace: jest.fn(),
  navigate: jest.fn(),
};

describe("LoginScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders correctly", () => {
    const { getByTestId, getByText } = render(
      <LoginScreen navigation={mockNavigation} />,
    );

    expect(getByTestId("login-screen")).toBeTruthy();
    expect(getByText("Nexora Mobile")).toBeTruthy();
    expect(getByText("Clinical Decision Support")).toBeTruthy();
  });

  it("shows validation errors for empty fields", () => {
    const { getByTestId, getByText } = render(
      <LoginScreen navigation={mockNavigation} />,
    );

    const loginButton = getByTestId("login-button");
    fireEvent.press(loginButton);

    expect(getByText("Username is required.")).toBeTruthy();
    expect(getByText("Password is required.")).toBeTruthy();
  });

  it("handles successful login", async () => {
    apiService.login.mockResolvedValue({
      success: true,
      token: "test-token",
    });

    const { getByTestId } = render(<LoginScreen navigation={mockNavigation} />);

    const usernameInput = getByTestId("username-input");
    const passwordInput = getByTestId("password-input");
    const loginButton = getByTestId("login-button");

    fireEvent.changeText(usernameInput, "clinician");
    fireEvent.changeText(passwordInput, "password123");
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(apiService.login).toHaveBeenCalledWith("clinician", "password123");
      expect(mockNavigation.replace).toHaveBeenCalledWith("Home");
    });
  });

  it("handles failed login", async () => {
    apiService.login.mockRejectedValue(new Error("Invalid credentials"));

    const { getByTestId } = render(<LoginScreen navigation={mockNavigation} />);

    const usernameInput = getByTestId("username-input");
    const passwordInput = getByTestId("password-input");
    const loginButton = getByTestId("login-button");

    fireEvent.changeText(usernameInput, "wrong");
    fireEvent.changeText(passwordInput, "wrong");
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Login Failed",
        expect.any(String),
      );
    });
  });

  it("disables login button while loading", async () => {
    apiService.login.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000)),
    );

    const { getByTestId } = render(<LoginScreen navigation={mockNavigation} />);

    const usernameInput = getByTestId("username-input");
    const passwordInput = getByTestId("password-input");
    const loginButton = getByTestId("login-button");

    fireEvent.changeText(usernameInput, "clinician");
    fireEvent.changeText(passwordInput, "password123");
    fireEvent.press(loginButton);

    // Button should be disabled during loading
    expect(loginButton.props.accessibilityState.disabled).toBe(true);
  });
});
