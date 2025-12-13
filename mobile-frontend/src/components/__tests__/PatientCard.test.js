import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { PatientCard } from "../PatientCard";
import { mockPatient } from "../../__mocks__/mockData";

describe("PatientCard", () => {
  const mockOnPress = jest.fn();
  const mockOnLongPress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders patient information correctly", () => {
    const { getByText, getByTestId } = render(
      <PatientCard
        patient={mockPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    expect(getByText(mockPatient.name)).toBeTruthy();
    expect(getByText(`Age: ${mockPatient.age}`)).toBeTruthy();
    expect(getByText(`MRN: ${mockPatient.mrn}`)).toBeTruthy();
    expect(getByTestId("risk-badge")).toBeTruthy();
  });

  it("handles press events", () => {
    const { getByTestId } = render(
      <PatientCard
        patient={mockPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    fireEvent.press(getByTestId("patient-card"));
    expect(mockOnPress).toHaveBeenCalledWith(mockPatient);
  });

  it("handles long press events", () => {
    const { getByTestId } = render(
      <PatientCard
        patient={mockPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    fireEvent(getByTestId("patient-card"), "longPress");
    expect(mockOnLongPress).toHaveBeenCalledWith(mockPatient);
  });

  it("displays risk level with correct color", () => {
    const highRiskPatient = { ...mockPatient, risk: 0.8 };
    const { getByText } = render(
      <PatientCard
        patient={highRiskPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    const riskText = getByText("80%");
    expect(riskText).toBeTruthy();
  });

  it("displays last updated time", () => {
    const patientWithUpdate = {
      ...mockPatient,
      lastUpdated: new Date().toISOString(),
    };
    const { getByText } = render(
      <PatientCard
        patient={patientWithUpdate}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    expect(getByText(/Last updated:/)).toBeTruthy();
  });

  it("handles missing optional data gracefully", () => {
    const minimalPatient = {
      id: "123",
      name: "John Doe",
      mrn: "MRN123",
    };

    const { getByText, queryByText } = render(
      <PatientCard
        patient={minimalPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    expect(getByText("John Doe")).toBeTruthy();
    expect(getByText("MRN: MRN123")).toBeTruthy();
    expect(queryByText(/Age:/)).toBeNull();
  });

  it("displays warning for outdated data", () => {
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 31); // 31 days old

    const { getByTestId } = render(
      <PatientCard
        patient={{ ...mockPatient, lastUpdated: oldDate.toISOString() }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    expect(getByTestId("outdated-warning")).toBeTruthy();
  });

  it("displays patient status indicator", () => {
    const { getByTestId } = render(
      <PatientCard
        patient={{ ...mockPatient, status: "active" }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    const statusIndicator = getByTestId("status-indicator");
    expect(statusIndicator).toBeTruthy();
  });

  it("displays N/A when risk is undefined", () => {
    const patientWithoutRisk = { ...mockPatient, risk: undefined };
    const { getByText } = render(
      <PatientCard
        patient={patientWithoutRisk}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />,
    );

    expect(getByText("N/A")).toBeTruthy();
  });
});
