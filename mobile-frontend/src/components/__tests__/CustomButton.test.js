import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import CustomButton from "../CustomButton";

describe("CustomButton", () => {
  it("renders correctly with title", () => {
    const { getByText } = render(<CustomButton title="Test Button" />);
    expect(getByText("Test Button")).toBeTruthy();
  });

  it("calls onPress when pressed", () => {
    const onPressMock = jest.fn();
    const { getByText } = render(
      <CustomButton title="Press Me" onPress={onPressMock} />,
    );

    fireEvent.press(getByText("Press Me"));
    expect(onPressMock).toHaveBeenCalledTimes(1);
  });

  it("does not call onPress when disabled", () => {
    const onPressMock = jest.fn();
    const { getByText } = render(
      <CustomButton title="Disabled" onPress={onPressMock} disabled />,
    );

    fireEvent.press(getByText("Disabled"));
    expect(onPressMock).not.toHaveBeenCalled();
  });

  it("shows loading indicator when loading", () => {
    const { queryByText, UNSAFE_getByType } = render(
      <CustomButton title="Loading" loading />,
    );

    expect(queryByText("Loading")).toBeNull();
    expect(UNSAFE_getByType("ActivityIndicator")).toBeTruthy();
  });

  it("is not pressable when loading", () => {
    const onPressMock = jest.fn();
    const { getByTestId } = render(
      <CustomButton
        title="Loading"
        onPress={onPressMock}
        loading
        testID="test-button"
      />,
    );

    fireEvent.press(getByTestId("test-button"));
    expect(onPressMock).not.toHaveBeenCalled();
  });

  it("applies custom styles", () => {
    const customStyle = { backgroundColor: "red" };
    const { getByTestId } = render(
      <CustomButton
        title="Styled"
        style={customStyle}
        testID="styled-button"
      />,
    );

    const button = getByTestID("styled-button");
    expect(button.props.style).toContainEqual(customStyle);
  });
});
