import React from "react";
import { render } from "@testing-library/react-native";
import App from "../../App";

// Mock the navigation container
jest.mock("@react-navigation/native", () => {
  const React = require("react");
  return {
    ...jest.requireActual("@react-navigation/native"),
    NavigationContainer: ({ children }) => <>{children}</>,
  };
});

jest.mock("@react-navigation/stack", () => {
  const React = require("react");
  return {
    createStackNavigator: () => ({
      Navigator: ({ children }) => <>{children}</>,
      Screen: () => null,
    }),
  };
});

// Mock AsyncStorage
jest.mock("@react-native-async-storage/async-storage", () => ({
  setItem: jest.fn(() => Promise.resolve()),
  getItem: jest.fn(() => Promise.resolve(null)),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

// Mock API service
jest.mock("../services/api", () => ({
  __esModule: true,
  default: {
    login: jest.fn(() => Promise.resolve({ success: true, token: "test" })),
    logout: jest.fn(() => Promise.resolve()),
    getPatients: jest.fn(() => Promise.resolve([])),
    getPatientDetails: jest.fn(() => Promise.resolve({})),
    getBaseURL: jest.fn(() => "http://localhost:8000"),
  },
}));

describe("App Component", () => {
  it("renders correctly", () => {
    const { getByTestId } = render(<App />);
    expect(getByTestId("app-container")).toBeTruthy();
  });

  it("renders without crashing", () => {
    expect(() => render(<App />)).not.toThrow();
  });
});
