import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { PatientCard } from '../PatientCard';
import { mockPatient } from '../../__mocks__/mockData';

describe('PatientCard', () => {
  const mockOnPress = jest.fn();
  const mockOnLongPress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders patient information correctly', () => {
    const { getByText, getByTestId } = render(
      <PatientCard
        patient={mockPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    expect(getByText(mockPatient.name)).toBeTruthy();
    expect(getByText(`Age: ${mockPatient.age}`)).toBeTruthy();
    expect(getByText(`MRN: ${mockPatient.mrn}`)).toBeTruthy();
    expect(getByTestId('risk-badge')).toBeTruthy();
  });

  it('handles press events', () => {
    const { getByTestId } = render(
      <PatientCard
        patient={mockPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    fireEvent.press(getByTestId('patient-card'));
    expect(mockOnPress).toHaveBeenCalledWith(mockPatient);
  });

  it('handles long press events', () => {
    const { getByTestId } = render(
      <PatientCard
        patient={mockPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    fireEvent(getByTestId('patient-card'), 'longPress');
    expect(mockOnLongPress).toHaveBeenCalledWith(mockPatient);
  });

  it('displays risk level with correct color', () => {
    const { getByTestId } = render(
      <PatientCard
        patient={{ ...mockPatient, riskLevel: 'high' }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    const riskBadge = getByTestId('risk-badge');
    expect(riskBadge.props.style).toMatchObject({
      backgroundColor: expect.stringMatching(/red|#ff0000/i)
    });
  });

  it('displays last updated time', () => {
    const lastUpdated = new Date().toISOString();
    const { getByText } = render(
      <PatientCard
        patient={{ ...mockPatient, lastUpdated }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    expect(getByText(/Last updated:/)).toBeTruthy();
  });

  it('handles missing optional data gracefully', () => {
    const minimalPatient = {
      id: '123',
      name: 'John Doe',
      mrn: 'MRN123'
    };

    const { getByText, queryByText } = render(
      <PatientCard
        patient={minimalPatient}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    expect(getByText('John Doe')).toBeTruthy();
    expect(getByText('MRN: MRN123')).toBeTruthy();
    expect(queryByText(/Age:/)).toBeNull();
  });

  it('displays warning for outdated data', () => {
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 31); // 31 days old

    const { getByTestId } = render(
      <PatientCard
        patient={{ ...mockPatient, lastUpdated: oldDate.toISOString() }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    expect(getByTestId('outdated-warning')).toBeTruthy();
  });

  it('handles different risk level displays', () => {
    const riskLevels = ['low', 'medium', 'high'];
    const { getByTestId, rerender } = render(
      <PatientCard
        patient={{ ...mockPatient, riskLevel: 'low' }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    riskLevels.forEach(level => {
      rerender(
        <PatientCard
          patient={{ ...mockPatient, riskLevel: level }}
          onPress={mockOnPress}
          onLongPress={mockOnLongPress}
        />
      );
      const riskBadge = getByTestId('risk-badge');
      expect(riskBadge.props.style).toBeTruthy();
    });
  });

  it('displays patient status indicator', () => {
    const { getByTestId } = render(
      <PatientCard
        patient={{ ...mockPatient, status: 'active' }}
        onPress={mockOnPress}
        onLongPress={mockOnLongPress}
      />
    );

    const statusIndicator = getByTestId('status-indicator');
    expect(statusIndicator).toBeTruthy();
    expect(statusIndicator.props.style).toMatchObject({
      backgroundColor: expect.stringMatching(/green|#00ff00/i)
    });
  });
});
