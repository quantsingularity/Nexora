import React from "react";
import { render } from "@testing-library/react-native";
import App from "../../App";

// Mock the navigation container
jest.mock("@react-navigation/native", () => {
  return {
    ...jest.requireActual("@react-navigation/native"),
    NavigationContainer: ({ children }) => children,
  };
});

jest.mock("@react-navigation/stack", () => ({
  createStackNavigator: () => ({
    Navigator: ({ children }) => children,
    Screen: ({ children }) => children,
  }),
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
