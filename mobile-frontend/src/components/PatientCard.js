import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Colors, Typography, Spacing } from "../theme/theme";
import Card from "./Card";

export const PatientCard = ({
  patient,
  onPress,
  onLongPress,
  testID = "patient-card",
}) => {
  const getRiskColor = (risk) => {
    if (risk > 0.7) return Colors.error;
    if (risk > 0.5) return Colors.warning;
    return Colors.success;
  };

  const getRiskLevel = (risk) => {
    if (risk > 0.7) return "high";
    if (risk > 0.5) return "medium";
    return "low";
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return Colors.success;
      case "inactive":
        return Colors.textSecondary;
      case "critical":
        return Colors.error;
      default:
        return Colors.textSecondary;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const isOutdated = (lastUpdated) => {
    if (!lastUpdated) return false;
    const date = new Date(lastUpdated);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    return diffDays > 30;
  };

  return (
    <TouchableOpacity
      onPress={() => onPress && onPress(patient)}
      onLongPress={() => onLongPress && onLongPress(patient)}
      testID={testID}
      activeOpacity={0.7}
    >
      <Card style={styles.card}>
        <View style={styles.container}>
          <View style={styles.mainInfo}>
            <View style={styles.headerRow}>
              <Text style={styles.patientName}>{patient.name}</Text>
              {patient.status && (
                <View
                  style={[
                    styles.statusIndicator,
                    { backgroundColor: getStatusColor(patient.status) },
                  ]}
                  testID="status-indicator"
                />
              )}
            </View>

            {patient.mrn && <Text style={styles.mrn}>MRN: {patient.mrn}</Text>}

            {patient.age && (
              <Text style={styles.details}>Age: {patient.age}</Text>
            )}

            {patient.lastUpdated && (
              <View style={styles.updateRow}>
                <Text style={styles.lastUpdated}>
                  Last updated: {formatDate(patient.lastUpdated)}
                </Text>
                {isOutdated(patient.lastUpdated) && (
                  <View style={styles.warningBadge} testID="outdated-warning">
                    <Text style={styles.warningText}>⚠</Text>
                  </View>
                )}
              </View>
            )}
          </View>

          <View style={styles.riskContainer}>
            <View
              style={[
                styles.riskBadge,
                {
                  backgroundColor:
                    patient.risk !== undefined
                      ? getRiskColor(patient.risk)
                      : Colors.textSecondary,
                },
              ]}
              testID="risk-badge"
            >
              <Text style={styles.riskValue}>
                {patient.risk !== undefined
                  ? `${Math.round(patient.risk * 100)}%`
                  : "N/A"}
              </Text>
              <Text style={styles.riskLabel}>Risk</Text>
            </View>
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 0,
  },
  container: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  mainInfo: {
    flex: 1,
    marginRight: Spacing.sm,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: Spacing.xs,
  },
  patientName: {
    ...Typography.body1,
    fontWeight: "600",
    color: Colors.text,
    flex: 1,
  },
  statusIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginLeft: Spacing.xs,
  },
  mrn: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  details: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  updateRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  lastUpdated: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontSize: 11,
  },
  warningBadge: {
    marginLeft: Spacing.xs,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: Colors.warning,
    justifyContent: "center",
    alignItems: "center",
  },
  warningText: {
    fontSize: 10,
    color: Colors.text,
  },
  riskContainer: {
    alignItems: "center",
  },
  riskBadge: {
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    borderRadius: 8,
    minWidth: 60,
    alignItems: "center",
  },
  riskValue: {
    ...Typography.h4,
    color: Colors.surface,
    fontWeight: "bold",
    fontSize: 18,
  },
  riskLabel: {
    ...Typography.caption,
    color: Colors.surface,
    fontSize: 10,
    marginTop: -2,
  },
});

export default PatientCard;
