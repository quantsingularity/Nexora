import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import CustomInput from "../CustomInput";

describe("CustomInput", () => {
  it("renders correctly", () => {
    const { getByPlaceholderText } = render(
      <CustomInput placeholder="Enter text" />,
    );
    expect(getByPlaceholderText("Enter text")).toBeTruthy();
  });

  it("displays label when provided", () => {
    const { getByText } = render(<CustomInput label="Username" />);
    expect(getByText("Username")).toBeTruthy();
  });

  it("calls onChangeText when text changes", () => {
    const onChangeTextMock = jest.fn();
    const { getByPlaceholderText } = render(
      <CustomInput placeholder="Type here" onChangeText={onChangeTextMock} />,
    );

    const input = getByPlaceholderText("Type here");
    fireEvent.changeText(input, "new text");
    expect(onChangeTextMock).toHaveBeenCalledWith("new text");
  });

  it("displays error message when error prop is provided", () => {
    const { getByText } = render(
      <CustomInput error="This field is required" />,
    );
    expect(getByText("This field is required")).toBeTruthy();
  });

  it("handles secure text entry", () => {
    const { getByPlaceholderText } = render(
      <CustomInput placeholder="Password" secureTextEntry />,
    );

    const input = getByPlaceholderText("Password");
    expect(input.props.secureTextEntry).toBe(true);
  });

  it("applies correct keyboard type", () => {
    const { getByPlaceholderText } = render(
      <CustomInput placeholder="Email" keyboardType="email-address" />,
    );

    const input = getByPlaceholderText("Email");
    expect(input.props.keyboardType).toBe("email-address");
  });

  it("shows correct value", () => {
    const { getByDisplayValue } = render(<CustomInput value="test value" />);
    expect(getByDisplayValue("test value")).toBeTruthy();
  });
});
