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
import api from "../services/api";
import { Colors, GlobalStyles, Spacing, Typography } from "../theme/theme";

const SEVERITY_META = {
  critical: { color: Colors.error, icon: "alert-circle" },
  warning: { color: Colors.warning, icon: "alert" },
  info: { color: Colors.info, icon: "information" },
};

const timeAgo = (iso) => {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 60) return `${Math.max(mins, 0)}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
};

const AlertsScreen = ({ navigation }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      setError(null);
      const data = await api.getNotifications();
      setNotifications(data.notifications || []);
    } catch (err) {
      setError(err.message || "Failed to load alerts.");
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

  const handleMarkRead = async (id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
    try {
      await api.markNotificationRead(id);
    } catch (err) {
      load();
    }
  };

  const handleMarkAllRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      await api.markAllNotificationsRead();
    } catch (err) {
      load();
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  if (loading) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper testID="alerts-screen">
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Alerts</Text>
          <Text style={styles.headerSubtitle}>
            {unreadCount} unread of {notifications.length}
          </Text>
        </View>
        {unreadCount > 0 && (
          <TouchableOpacity onPress={handleMarkAllRead}>
            <Text style={styles.markAllText}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>

      {error && (
        <Card style={styles.errorCard}>
          <Text style={styles.errorText}>{error}</Text>
          <CustomButton title="Retry" onPress={() => load()} />
        </Card>
      )}

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
        {notifications.length === 0 && !error ? (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons
              name="check-circle-outline"
              size={40}
              color={Colors.success}
            />
            <Text style={styles.emptyText}>
              All caught up. No alerts right now.
            </Text>
          </View>
        ) : (
          notifications.map((n) => {
            const meta = SEVERITY_META[n.severity] || SEVERITY_META.info;
            return (
              <TouchableOpacity
                key={n.id}
                onPress={() => {
                  if (!n.read) handleMarkRead(n.id);
                  if (n.patient_id) {
                    navigation.navigate("PatientsTab", {
                      screen: "PatientDetail",
                      params: {
                        patientId: n.patient_id,
                        patientName: undefined,
                      },
                    });
                  }
                }}
              >
                <Card
                  style={[styles.alertCard, !n.read && styles.alertCardUnread]}
                >
                  <View style={styles.alertRow}>
                    <View
                      style={[
                        styles.alertIcon,
                        { backgroundColor: `${meta.color}1A` },
                      ]}
                    >
                      <MaterialCommunityIcons
                        name={meta.icon}
                        size={20}
                        color={meta.color}
                      />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.alertTitle}>{n.title}</Text>
                      <Text style={styles.alertMessage}>{n.message}</Text>
                      <Text style={styles.alertTime}>
                        {timeAgo(n.created_at)}
                      </Text>
                    </View>
                    {!n.read && <View style={styles.unreadDot} />}
                  </View>
                </Card>
              </TouchableOpacity>
            );
          })
        )}
        <View style={{ height: Spacing.xl }} />
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.md,
  },
  headerTitle: { ...Typography.h3, color: Colors.text },
  headerSubtitle: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  markAllText: {
    ...Typography.body2,
    color: Colors.primary,
    fontWeight: "700",
  },
  errorCard: { backgroundColor: "#FEF2F2", marginBottom: Spacing.sm },
  errorText: {
    ...Typography.body2,
    color: Colors.error,
    marginBottom: Spacing.sm,
  },
  emptyState: { alignItems: "center", marginTop: Spacing.xxl },
  emptyText: {
    ...Typography.body1,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
  },
  alertCard: { padding: Spacing.md },
  alertCardUnread: { backgroundColor: "rgba(37, 99, 235, 0.04)" },
  alertRow: { flexDirection: "row", alignItems: "flex-start" },
  alertIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginRight: Spacing.sm,
  },
  alertTitle: { ...Typography.body2, fontWeight: "700", color: Colors.text },
  alertMessage: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  alertTime: { ...Typography.caption, color: Colors.disabled, marginTop: 4 },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
    marginTop: 6,
  },
});

export default AlertsScreen;
