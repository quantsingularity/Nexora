import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Dimensions,
  RefreshControl,
} from "react-native";
import { LineChart } from "react-native-chart-kit";
import { Colors, Typography, Spacing, GlobalStyles } from "../theme/theme";
import ScreenWrapper from "../components/ScreenWrapper";
import Card from "../components/Card";
import apiService from "../services/api";

const PatientDetailScreen = ({ route, navigation }) => {
  const { patientId, patientName } = route.params;
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadDetails = async (isRefreshing = false) => {
    try {
      if (!isRefreshing) setLoading(true);
      setError(null);

      const patientDetails = await apiService.getPatientDetails(patientId);
      setDetails(patientDetails);
    } catch (error) {
      console.error("Failed to load patient details:", error);
      setError("Failed to load patient details. Please try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    navigation.setOptions({ title: patientName || "Prediction Details" });
    loadDetails();
  }, [patientId, patientName, navigation]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadDetails(true);
  };

  if (loading) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  if (error || !details) {
    return (
      <ScreenWrapper style={GlobalStyles.centered} testID="patient-details">
        <Text style={Typography.body1} testID="error-message">
          {error || "Could not load patient details."}
        </Text>
      </ScreenWrapper>
    );
  }

  const getRiskColor = (risk) => {
    if (risk > 0.7) return Colors.error;
    if (risk > 0.5) return Colors.warning;
    return Colors.success;
  };

  const chartConfig = {
    backgroundGradientFrom: Colors.surface,
    backgroundGradientFromOpacity: 1,
    backgroundGradientTo: Colors.surface,
    backgroundGradientToOpacity: 1,
    color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    strokeWidth: 2,
    barPercentage: 0.5,
    useShadows: false,
    propsForLabels: {
      fontSize: 10,
    },
  };

  const shapData = {
    labels: details.predictions.shap_features.slice(0, 5),
    datasets: [
      {
        data: details.predictions.shap_values.slice(0, 5),
        color: (opacity = 1) => `rgba(88, 86, 214, ${opacity})`,
        strokeWidth: 2,
      },
    ],
    legend: ["SHAP Value Impact"],
  };

  return (
    <ScreenWrapper testID="patient-details">
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContainer}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[Colors.primary]}
            tintColor={Colors.primary}
          />
        }
      >
        <Card style={styles.riskCard}>
          <Text style={styles.sectionTitle}>Overall Risk Score</Text>
          <Text
            style={[styles.riskText, { color: getRiskColor(details.risk) }]}
            testID="risk-score"
          >
            {`${(details.risk * 100).toFixed(0)}%`}
          </Text>
          <Text style={styles.subText}>
            Confidence: [
            {`${(details.uncertainty.confidence_interval[0] * 100).toFixed(0)}%`}{" "}
            -{" "}
            {`${(details.uncertainty.confidence_interval[1] * 100).toFixed(0)}%`}
            ]
          </Text>
          {details.name && (
            <Text style={styles.patientNameText} testID="patient-name">
              {details.name}
            </Text>
          )}
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Risk Factor Importance (SHAP)</Text>
          <LineChart
            data={shapData}
            width={
              Dimensions.get("window").width - Spacing.md * 2 - Spacing.md * 2
            }
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
            yAxisLabel="Impact "
            yAxisSuffix=""
            fromZero
            segments={4}
            testID="risk-chart"
          />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Key Contributing Factors</Text>
          {details.predictions.top_features.map((feature, index) => (
            <View key={index} style={styles.listItemContainer}>
              <Text style={styles.bulletPoint}>•</Text>
              <Text style={styles.listItemText}>{feature}</Text>
            </View>
          ))}
        </Card>

        <Card testID="clinical-history-list">
          <Text style={styles.sectionTitle}>Patient Timeline</Text>
          {details.timeline && details.timeline.length > 0 ? (
            details.timeline.map((event, index) => (
              <View key={index} style={styles.timelineItem}>
                <Text style={styles.timelineDate}>{event.date}:</Text>
                <Text style={styles.timelineEvent}>{event.event}</Text>
              </View>
            ))
          ) : (
            <Text style={styles.noDataText}>No timeline data available.</Text>
          )}
        </Card>
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  scrollContainer: {
    paddingBottom: Spacing.md,
  },
  riskCard: {
    alignItems: "center",
    backgroundColor: Colors.surface,
  },
  sectionTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.md,
    alignSelf: "flex-start",
  },
  riskText: {
    ...Typography.h1,
    fontSize: 48,
    fontWeight: "bold",
    marginBottom: Spacing.xs,
  },
  subText: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  patientNameText: {
    ...Typography.body1,
    color: Colors.text,
    fontWeight: "600",
  },
  chart: {
    borderRadius: 8,
    marginTop: Spacing.sm,
  },
  listItemContainer: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: Spacing.sm,
  },
  bulletPoint: {
    ...Typography.body1,
    color: Colors.primary,
    marginRight: Spacing.sm,
    lineHeight: Typography.body1.fontSize * 1.4,
  },
  listItemText: {
    ...Typography.body1,
    color: Colors.text,
    flex: 1,
    lineHeight: Typography.body1.fontSize * 1.4,
  },
  timelineItem: {
    flexDirection: "row",
    marginBottom: Spacing.sm,
    alignItems: "flex-start",
  },
  timelineDate: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: "600",
    width: 90,
  },
  timelineEvent: {
    ...Typography.body2,
    color: Colors.text,
    flex: 1,
  },
  noDataText: {
    ...Typography.body2,
    color: Colors.textSecondary,
    fontStyle: "italic",
  },
});

export default PatientDetailScreen;
