// Jest setup file for Nexora Mobile Frontend
// This file runs before each test suite

// Setup jest-expo preset which handles most React Native mocks
require("@testing-library/react-native/extend-expect");

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

// Mock axios
jest.mock("axios", () => {
  const mockAxios = {
    create: jest.fn(function () {
      return {
        get: jest.fn(() => Promise.resolve({ data: [] })),
        post: jest.fn(() => Promise.resolve({ data: {} })),
        interceptors: {
          request: {
            use: jest.fn((onFulfilled) => onFulfilled),
            eject: jest.fn(),
          },
          response: {
            use: jest.fn((onFulfilled) => onFulfilled),
            eject: jest.fn(),
          },
        },
      };
    }),
    get: jest.fn(() => Promise.resolve({ data: [] })),
    post: jest.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: {
        use: jest.fn(),
        eject: jest.fn(),
      },
      response: {
        use: jest.fn(),
        eject: jest.fn(),
      },
    },
  };
  return mockAxios;
});

// Suppress console warnings/errors during tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
};
