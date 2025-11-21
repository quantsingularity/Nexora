import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Dimensions,
} from "react-native";
import { LineChart } from "react-native-chart-kit";
import { Colors, Typography, Spacing, GlobalStyles } from "../theme/theme";
import ScreenWrapper from "../components/ScreenWrapper";
import Card from "../components/Card";

// Mock API service - replace with actual API calls later
const mockApiService = {
  getPatientDetails: async (patientId) => {
    await new Promise((resolve) => setTimeout(resolve, 700));
    if (patientId === "p001") {
      return {
        id: "p001",
        name: "John Doe",
        risk: 0.75,
        predictions: {
          risk: 0.75,
          top_features: [
            "age > 60",
            "previous_admissions > 2",
            "diabetes diagnosis",
          ],
          cohort_size: 120,
          shap_features: ["Age", "Prev Adm", "Diabetes", "HTN", "HF"],
          shap_values: [0.3, 0.25, 0.2, 0.15, 0.1],
        },
        explanations: { method: "SHAP", values: [0.3, 0.25, 0.2, 0.15, 0.1] },
        uncertainty: { confidence_interval: [0.65, 0.85] },
        timeline: [
          { event: "Admission", date: "2024-04-10" },
          { event: "Lab Test (High Glucose)", date: "2024-04-11" },
          { event: "Diagnosis: HF", date: "2024-04-12" },
          { event: "Discharge", date: "2024-04-18" },
        ],
      };
    } else if (patientId === "p003") {
      return {
        id: "p003",
        name: "Robert Johnson",
        risk: 0.85,
        predictions: {
          risk: 0.85,
          top_features: [
            "multiple comorbidities",
            "age > 55",
            "lab_value_x abnormal",
          ],
          cohort_size: 95,
          shap_features: ["Comorb", "Age", "Lab X", "Med Y", "Prev Adm"],
          shap_values: [0.4, 0.2, 0.15, 0.05, 0.05],
        },
        explanations: { method: "SHAP", values: [0.4, 0.2, 0.15, 0.05, 0.05] },
        uncertainty: { confidence_interval: [0.78, 0.92] },
        timeline: [
          { event: "Admission", date: "2024-04-05" },
          { event: "Surgery", date: "2024-04-07" },
          { event: "ICU Stay", date: "2024-04-08" },
          { event: "Discharge", date: "2024-04-20" },
        ],
      };
    }
    // Default mock data for other patients
    return {
      id: patientId,
      name: "Default Patient",
      risk: 0.55,
      predictions: {
        risk: 0.55,
        top_features: ["feature_a", "feature_b", "feature_c"],
        cohort_size: 150,
        shap_features: ["Feat A", "Feat B", "Feat C", "Feat D", "Feat E"],
        shap_values: [0.2, 0.15, 0.1, 0.05, 0.05],
      },
      explanations: { method: "SHAP", values: [0.2, 0.15, 0.1, 0.05, 0.05] },
      uncertainty: { confidence_interval: [0.45, 0.65] },
      timeline: [],
    };
  },
};

const PatientDetailScreen = ({ route, navigation }) => {
  const { patientId, patientName } = route.params;
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    navigation.setOptions({ title: patientName || "Prediction Details" }); // Set header title dynamically
    const loadDetails = async () => {
      setLoading(true);
      try {
        const patientDetails =
          await mockApiService.getPatientDetails(patientId);
        setDetails(patientDetails);
      } catch (error) {
        console.error("Failed to load patient details:", error);
        // Consider adding user-facing error feedback
      } finally {
        setLoading(false);
      }
    };
    loadDetails();
  }, [patientId, patientName, navigation]);

  if (loading) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  if (!details) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <Text style={Typography.body1}>Could not load patient details.</Text>
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
    color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`, // Colors.primary
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`, // Colors.text
    strokeWidth: 2, // optional, default 3
    barPercentage: 0.5,
    useShadows: false, // Optional: add shadows to bars
    propsForLabels: {
      fontSize: 10, // Smaller font size for labels
    },
  };

  const shapData = {
    labels: details.predictions.shap_features.slice(0, 5), // Top 5 features
    datasets: [
      {
        data: details.predictions.shap_values.slice(0, 5),
        color: (opacity = 1) => `rgba(88, 86, 214, ${opacity})`, // Colors.secondary
        strokeWidth: 2, // optional
      },
    ],
    legend: ["SHAP Value Impact"], // optional
  };

  return (
    <ScreenWrapper>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContainer}
      >
        <Card style={styles.riskCard}>
          <Text style={styles.sectionTitle}>Overall Risk Score</Text>
          <Text
            style={[styles.riskText, { color: getRiskColor(details.risk) }]}
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
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Risk Factor Importance (SHAP)</Text>
          <LineChart
            data={shapData}
            width={
              Dimensions.get("window").width - Spacing.md * 2 - Spacing.md * 2
            } // Screen width - screen padding - card padding
            height={220}
            chartConfig={chartConfig}
            bezier // Makes the line chart smooth
            style={styles.chart}
            yAxisLabel="Impact "
            yAxisSuffix=""
            fromZero // Start y-axis from 0
            segments={4} // Number of horizontal grid lines
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

        <Card>
          <Text style={styles.sectionTitle}>Patient Timeline</Text>
          {details.timeline.length > 0 ? (
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
    paddingBottom: Spacing.md, // Ensure space at the bottom
  },
  riskCard: {
    alignItems: "center",
    backgroundColor: Colors.surface, // Ensure card background
  },
  sectionTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.md,
    alignSelf: "flex-start",
  },
  riskText: {
    ...Typography.h1,
    fontSize: 48, // Larger font size for emphasis
    fontWeight: "bold",
    marginBottom: Spacing.xs,
  },
  subText: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
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
    lineHeight: Typography.body1.fontSize * 1.4, // Adjust line height for alignment
  },
  listItemText: {
    ...Typography.body1,
    color: Colors.text,
    flex: 1, // Allow text to wrap
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
    width: 90, // Fixed width for date alignment
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
