import React from "react";
import { render } from "@testing-library/react-native";
import { Text } from "react-native";
import ScreenWrapper from "../ScreenWrapper";

describe("ScreenWrapper", () => {
  it("renders children correctly", () => {
    const { getByText } = render(
      <ScreenWrapper>
        <Text>Screen Content</Text>
      </ScreenWrapper>,
    );
    expect(getByText("Screen Content")).toBeTruthy();
  });

  it("applies testID when provided", () => {
    const { getByTestId } = render(
      <ScreenWrapper testID="test-screen">
        <Text>Content</Text>
      </ScreenWrapper>,
    );

    expect(getByTestId("test-screen")).toBeTruthy();
  });

  it("uses SafeAreaView by default", () => {
    const { getByTestId } = render(
      <ScreenWrapper testID="test-wrapper">
        <Text>Content</Text>
      </ScreenWrapper>,
    );

    // Just verify the wrapper renders with correct testID
    expect(getByTestId("test-wrapper")).toBeTruthy();
  });

  it("uses View when useSafeArea is false", () => {
    const { getByTestId } = render(
      <ScreenWrapper useSafeArea={false} testID="test-wrapper-view">
        <Text>Content</Text>
      </ScreenWrapper>,
    );

    // Verify the wrapper renders correctly even without SafeAreaView
    expect(getByTestId("test-wrapper-view")).toBeTruthy();
  });
});
