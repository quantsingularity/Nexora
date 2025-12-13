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
    const { UNSAFE_getByType } = render(
      <ScreenWrapper>
        <Text>Content</Text>
      </ScreenWrapper>,
    );

    expect(UNSAFE_getByType("SafeAreaView")).toBeTruthy();
  });

  it("uses View when useSafeArea is false", () => {
    const { UNSAFE_queryByType } = render(
      <ScreenWrapper useSafeArea={false}>
        <Text>Content</Text>
      </ScreenWrapper>,
    );

    expect(UNSAFE_queryByType("SafeAreaView")).toBeNull();
  });
});
