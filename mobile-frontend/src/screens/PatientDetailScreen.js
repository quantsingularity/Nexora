import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Card from "../components/Card";
import CustomButton from "../components/CustomButton";
import ScreenWrapper from "../components/ScreenWrapper";
import api from "../services/api";
import {
  Colors,
  GlobalStyles,
  Spacing,
  Typography,
  getRiskColor,
  getRiskLabel,
} from "../theme/theme";

const PatientDetailScreen = ({ route, navigation }) => {
  const { patientId, patientName } = route.params;
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [error, setError] = useState(null);

  const loadDetails = useCallback(
    async (isRefreshing = false) => {
      try {
        if (!isRefreshing) setLoading(true);
        setError(null);
        const details = await api.getPatientDetails(patientId);
        setPatient(details);
      } catch (err) {
        setError(err.message || "Failed to load patient details.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [patientId],
  );

  useEffect(() => {
    navigation.setOptions({ title: patientName || "Patient Detail" });
    loadDetails();
  }, [loadDetails, navigation, patientName]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadDetails(true);
  };

  const handleRecompute = async () => {
    setRecomputing(true);
    try {
      const updated = await api.recomputeRisk(patientId);
      setPatient(updated);
    } catch (err) {
      setError(err.message || "Failed to recompute risk score.");
    } finally {
      setRecomputing(false);
    }
  };

  if (loading) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  if (error && !patient) {
    return (
      <ScreenWrapper style={GlobalStyles.centered} testID="patient-details">
        <Text style={Typography.body1} testID="error-message">
          {error}
        </Text>
        <CustomButton
          title="Retry"
          onPress={() => loadDetails()}
          style={{ marginTop: Spacing.md }}
        />
      </ScreenWrapper>
    );
  }

  if (!patient) return null;

  const riskColor = getRiskColor(patient.riskScore);
  const maxImpact = Math.max(
    ...(patient.riskFactors || []).map((f) => f.impact),
    0.01,
  );

  return (
    <ScreenWrapper testID="patient-details">
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContainer}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.primary}
          />
        }
      >
        <Card style={styles.riskCard}>
          <Text style={styles.sectionTitle}>Readmission Risk Score</Text>
          <Text
            style={[styles.riskText, { color: riskColor }]}
            testID="risk-score"
          >
            {`${Math.round((patient.riskScore || 0) * 100)}%`}
          </Text>
          <View
            style={[styles.riskPill, { backgroundColor: `${riskColor}1A` }]}
          >
            <Text style={[styles.riskPillText, { color: riskColor }]}>
              {getRiskLabel(patient.riskScore)} risk
            </Text>
          </View>
          {patient.name && (
            <Text style={styles.patientNameText} testID="patient-name">
              {patient.name} · Age {patient.age} · {patient.gender}
            </Text>
          )}
          <CustomButton
            title={recomputing ? "Recomputing…" : "Recompute Risk Score"}
            onPress={handleRecompute}
            loading={recomputing}
            style={styles.recomputeButton}
          />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Risk Factors</Text>
          {(patient.riskFactors || []).map((factor, index) => (
            <View key={index} style={styles.factorRow}>
              <View style={styles.factorHeader}>
                <Text style={styles.factorName}>{factor.name}</Text>
                <Text style={styles.factorImpact}>
                  {Math.round(factor.impact * 100)}%
                </Text>
              </View>
              <View style={styles.factorTrack}>
                <View
                  style={[
                    styles.factorFill,
                    {
                      width: `${(factor.impact / maxImpact) * 100}%`,
                      backgroundColor: Colors.primary,
                    },
                  ]}
                />
              </View>
            </View>
          ))}
          {(!patient.riskFactors || patient.riskFactors.length === 0) && (
            <Text style={styles.noDataText}>
              No risk factor data available.
            </Text>
          )}
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Recommended Interventions</Text>
          {(patient.interventions || []).map((item, index) => (
            <View key={index} style={styles.listItemContainer}>
              <MaterialCommunityIcons
                name="clipboard-check-outline"
                size={18}
                color={Colors.secondary}
                style={{ marginRight: Spacing.sm, marginTop: 2 }}
              />
              <View style={{ flex: 1 }}>
                <Text style={styles.listItemText}>{item.name}</Text>
                <Text style={styles.listItemSubtext}>{item.description}</Text>
              </View>
            </View>
          ))}
          {(!patient.interventions || patient.interventions.length === 0) && (
            <Text style={styles.noDataText}>No interventions recommended.</Text>
          )}
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Current Medications</Text>
          {(patient.medications || []).map((med, index) => (
            <View key={index} style={styles.listItemContainer}>
              <MaterialCommunityIcons
                name="pill"
                size={18}
                color={Colors.textSecondary}
                style={{ marginRight: Spacing.sm, marginTop: 2 }}
              />
              <Text style={styles.listItemText}>
                {med.name}: {med.dosage}, {med.frequency}
              </Text>
            </View>
          ))}
          {(!patient.medications || patient.medications.length === 0) && (
            <Text style={styles.noDataText}>No medications on record.</Text>
          )}
        </Card>

        <Card testID="clinical-history-list">
          <Text style={styles.sectionTitle}>Patient Timeline</Text>
          {patient.timeline && patient.timeline.length > 0 ? (
            patient.timeline.map((event, index) => (
              <View key={index} style={styles.timelineItem}>
                <Text style={styles.timelineDate}>{event.date}</Text>
                <Text style={styles.timelineEvent}>
                  {event.title || event.description}
                </Text>
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
  scrollContainer: { paddingBottom: Spacing.xl },
  riskCard: { alignItems: "center" },
  sectionTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.md,
    alignSelf: "flex-start",
  },
  riskText: { fontSize: 48, fontWeight: "800", marginBottom: Spacing.xs },
  riskPill: {
    paddingHorizontal: Spacing.md,
    paddingVertical: 4,
    borderRadius: 999,
    marginBottom: Spacing.sm,
  },
  riskPillText: { ...Typography.caption, fontWeight: "700" },
  patientNameText: {
    ...Typography.body1,
    color: Colors.text,
    fontWeight: "600",
    marginBottom: Spacing.sm,
  },
  recomputeButton: { marginTop: Spacing.sm, width: "100%" },
  factorRow: { marginBottom: Spacing.md },
  factorHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  factorName: { ...Typography.body2, color: Colors.text, fontWeight: "600" },
  factorImpact: { ...Typography.caption, color: Colors.textSecondary },
  factorTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.surfaceAlt,
    overflow: "hidden",
  },
  factorFill: { height: 6, borderRadius: 3 },
  listItemContainer: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: Spacing.md,
  },
  listItemText: { ...Typography.body2, color: Colors.text, fontWeight: "600" },
  listItemSubtext: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  timelineItem: { marginBottom: Spacing.md },
  timelineDate: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: "600",
  },
  timelineEvent: { ...Typography.body2, color: Colors.text, marginTop: 2 },
  noDataText: {
    ...Typography.body2,
    color: Colors.textSecondary,
    fontStyle: "italic",
  },
});

export default PatientDetailScreen;
