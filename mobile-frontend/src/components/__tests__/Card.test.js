import React from "react";
import { render } from "@testing-library/react-native";
import { Text } from "react-native";
import Card from "../Card";

describe("Card", () => {
  it("renders children correctly", () => {
    const { getByText } = render(
      <Card>
        <Text>Card Content</Text>
      </Card>,
    );
    expect(getByText("Card Content")).toBeTruthy();
  });

  it("applies custom styles", () => {
    const customStyle = { backgroundColor: "blue" };
    const { getByTestId } = render(
      <Card style={customStyle} testID="test-card">
        <Text>Content</Text>
      </Card>,
    );

    const card = getByTestId("test-card");
    expect(card.props.style).toContainEqual(customStyle);
  });

  it("renders multiple children", () => {
    const { getByText } = render(
      <Card>
        <Text>First</Text>
        <Text>Second</Text>
      </Card>,
    );

    expect(getByText("First")).toBeTruthy();
    expect(getByText("Second")).toBeTruthy();
  });
});
