// Jest setup file for Nexora Mobile Frontend
// This file runs before each test suite

// Mock @react-native-async-storage/async-storage
import mockAsyncStorage from "@react-native-async-storage/async-storage/jest/async-storage-mock";
jest.mock("@react-native-async-storage/async-storage", () => mockAsyncStorage);

// Mock expo-constants
jest.mock("expo-constants", () => ({
  expoConfig: {
    extra: {
      apiBaseUrl: "http://localhost:8000",
    },
  },
}));

// Mock react-native-chart-kit
jest.mock("react-native-chart-kit", () => ({
  LineChart: "LineChart",
  BarChart: "BarChart",
  PieChart: "PieChart",
  ProgressChart: "ProgressChart",
  ContributionGraph: "ContributionGraph",
  StackedBarChart: "StackedBarChart",
}));

// Mock react-native-svg
jest.mock("react-native-svg", () => ({
  Svg: "Svg",
  Circle: "Circle",
  Rect: "Rect",
  Path: "Path",
  G: "G",
  Text: "Text",
  Line: "Line",
  Polygon: "Polygon",
  Polyline: "Polyline",
  Ellipse: "Ellipse",
  ClipPath: "ClipPath",
  Defs: "Defs",
  LinearGradient: "LinearGradient",
  RadialGradient: "RadialGradient",
  Stop: "Stop",
}));

// Mock gesture handler
jest.mock("react-native-gesture-handler", () => {
  const View = require("react-native/Libraries/Components/View/View");
  return {
    GestureHandlerRootView: View,
    gestureHandlerRootHOC: (Component) => Component,
    PanGestureHandler: View,
    TapGestureHandler: View,
    State: {},
    Directions: {},
  };
});

// Mock Alert
jest.mock("react-native/Libraries/Alert/Alert", () => ({
  alert: jest.fn(),
}));

// Mock axios
jest.mock("axios", () => {
  const mockAxios = {
    create: jest.fn(() => mockAxios),
    get: jest.fn(),
    post: jest.fn(),
    interceptors: {
      request: {
        use: jest.fn(),
      },
      response: {
        use: jest.fn(),
      },
    },
  };
  return mockAxios;
});

// Suppress console warnings during tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
};
