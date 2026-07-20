import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Card from "../components/Card";
import CustomButton from "../components/CustomButton";
import ScreenWrapper from "../components/ScreenWrapper";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import {
  Colors,
  GlobalStyles,
  Radius,
  Spacing,
  Typography,
} from "../theme/theme";

const StatTile = ({ icon, label, value, color }) => (
  <Card style={styles.statTile}>
    <View style={[styles.statIconWrap, { backgroundColor: `${color}1A` }]}>
      <MaterialCommunityIcons name={icon} size={20} color={color} />
    </View>
    <Text style={styles.statValue}>{value}</Text>
    <Text style={styles.statLabel}>{label}</Text>
  </Card>
);

const RiskBar = ({ label, count, total, color }) => {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <View style={styles.riskBarRow}>
      <View style={styles.riskBarHeader}>
        <Text style={styles.riskBarLabel}>{label}</Text>
        <Text style={styles.riskBarValue}>
          {count} · {pct}%
        </Text>
      </View>
      <View style={styles.riskBarTrack}>
        <View
          style={[
            styles.riskBarFill,
            { width: `${pct}%`, backgroundColor: color },
          ]}
        />
      </View>
    </View>
  );
};

const DashboardScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      setError(null);
      const summary = await api.getDashboardData();
      setData(summary);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleRefresh = () => {
    setRefreshing(true);
    load(true);
  };

  if (loading) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  if (error && !data) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <MaterialCommunityIcons
          name="alert-circle-outline"
          size={40}
          color={Colors.error}
        />
        <Text style={styles.errorText}>{error}</Text>
        <CustomButton
          title="Retry"
          onPress={() => load()}
          style={{ marginTop: Spacing.md }}
        />
      </ScreenWrapper>
    );
  }

  const { stats, patientRiskDistribution } = data;
  const totalRisk =
    (patientRiskDistribution?.highRisk || 0) +
    (patientRiskDistribution?.mediumRisk || 0) +
    (patientRiskDistribution?.lowRisk || 0);

  return (
    <ScreenWrapper testID="dashboard-screen">
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <Text style={styles.welcomeText}>
            {user?.full_name
              ? `Welcome back, ${user.full_name.split(" ")[0]}`
              : "Dashboard"}
          </Text>
          <Text style={styles.headerSubtitle}>
            Overview of your patient population
          </Text>
        </View>

        <View style={styles.statsGrid}>
          <StatTile
            icon="account-group-outline"
            label="Active Patients"
            value={stats.activePatients}
            color={Colors.primary}
          />
          <StatTile
            icon="alert-outline"
            label="High Risk"
            value={stats.highRiskPatients}
            color={Colors.error}
          />
          <StatTile
            icon="calendar-clock-outline"
            label="Avg. Stay (days)"
            value={stats.avgLengthOfStay}
            color={Colors.secondary}
          />
          <StatTile
            icon="brain"
            label="Active Models"
            value={stats.activeModels}
            color={Colors.info}
          />
        </View>

        <Card>
          <Text style={styles.sectionTitle}>Risk Distribution</Text>
          <RiskBar
            label="High Risk"
            count={patientRiskDistribution.highRisk}
            total={totalRisk}
            color={Colors.error}
          />
          <RiskBar
            label="Medium Risk"
            count={patientRiskDistribution.mediumRisk}
            total={totalRisk}
            color={Colors.warning}
          />
          <RiskBar
            label="Low Risk"
            count={patientRiskDistribution.lowRisk}
            total={totalRisk}
            color={Colors.success}
          />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <TouchableOpacity
            style={styles.quickAction}
            onPress={() =>
              navigation.navigate("PatientsTab", {
                screen: "PatientList",
                params: { risk: "high" },
              })
            }
          >
            <MaterialCommunityIcons
              name="account-alert-outline"
              size={20}
              color={Colors.error}
            />
            <Text style={styles.quickActionText}>View high-risk patients</Text>
            <MaterialCommunityIcons
              name="chevron-right"
              size={20}
              color={Colors.textSecondary}
            />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickAction}
            onPress={() => navigation.navigate("AlertsTab")}
          >
            <MaterialCommunityIcons
              name="bell-outline"
              size={20}
              color={Colors.primary}
            />
            <Text style={styles.quickActionText}>Review alerts</Text>
            <MaterialCommunityIcons
              name="chevron-right"
              size={20}
              color={Colors.textSecondary}
            />
          </TouchableOpacity>
        </Card>

        <View style={{ height: Spacing.xl }} />
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  header: {
    marginBottom: Spacing.md,
  },
  welcomeText: {
    ...Typography.h3,
    color: Colors.text,
  },
  headerSubtitle: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  statTile: {
    width: "48%",
  },
  statIconWrap: {
    width: 36,
    height: 36,
    borderRadius: Radius.sm,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.sm,
  },
  statValue: {
    ...Typography.h3,
    color: Colors.text,
  },
  statLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  sectionTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  riskBarRow: {
    marginBottom: Spacing.md,
  },
  riskBarHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  riskBarLabel: {
    ...Typography.body2,
    color: Colors.text,
    fontWeight: "600",
  },
  riskBarValue: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
  riskBarTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.surfaceAlt,
    overflow: "hidden",
  },
  riskBarFill: {
    height: 8,
    borderRadius: 4,
  },
  quickAction: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: Spacing.sm + 2,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  quickActionText: {
    ...Typography.body2,
    color: Colors.text,
    flex: 1,
    marginLeft: Spacing.sm,
  },
  errorText: {
    ...Typography.body1,
    color: Colors.textSecondary,
    textAlign: "center",
    marginTop: Spacing.sm,
    paddingHorizontal: Spacing.lg,
  },
});

export default DashboardScreen;
