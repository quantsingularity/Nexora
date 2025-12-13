import React, { useState, useEffect, useMemo } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Modal,
  Pressable,
  RefreshControl,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Colors, Typography, Spacing, GlobalStyles } from "../theme/theme";
import ScreenWrapper from "../components/ScreenWrapper";
import Card from "../components/Card";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import apiService from "../services/api";

const SORT_OPTIONS = {
  NAME_ASC: { label: "Name (A-Z)", key: "name_asc" },
  NAME_DESC: { label: "Name (Z-A)", key: "name_desc" },
  RISK_DESC: { label: "Risk (High-Low)", key: "risk_desc" },
  RISK_ASC: { label: "Risk (Low-High)", key: "risk_asc" },
  UPDATE_DESC: { label: "Last Update (Newest)", key: "update_desc" },
};

const FILTER_OPTIONS = {
  ALL: { label: "All Patients", key: "all" },
  HIGH_RISK: { label: "High Risk (>70%)", key: "high_risk" },
  MEDIUM_RISK: { label: "Medium Risk (50-70%)", key: "medium_risk" },
  LOW_RISK: { label: "Low Risk (<50%)", key: "low_risk" },
};

const HomeScreen = ({ navigation }) => {
  const [allPatients, setAllPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [username, setUsername] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortOption, setSortOption] = useState(SORT_OPTIONS.RISK_DESC.key);
  const [filterOption, setFilterOption] = useState(FILTER_OPTIONS.ALL.key);
  const [isSortModalVisible, setSortModalVisible] = useState(false);
  const [isFilterModalVisible, setFilterModalVisible] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async (isRefreshing = false) => {
    try {
      if (!isRefreshing) setLoading(true);
      setError(null);

      const storedUsername = await AsyncStorage.getItem("username");
      setUsername(storedUsername || "Clinician");

      const patientData = await apiService.getPatients();
      setAllPatients(patientData);
    } catch (error) {
      console.error("Failed to load data:", error);
      setError("Failed to load patients. Please try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData(true);
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
    } catch (error) {
      console.error("Logout error:", error);
    }
    navigation.replace("Login");
  };

  const getRiskColor = (risk) => {
    if (risk > 0.7) return Colors.error;
    if (risk > 0.5) return Colors.warning;
    return Colors.success;
  };

  const filteredAndSortedPatients = useMemo(() => {
    let patients = [...allPatients];

    // Apply search filter
    if (searchTerm.trim()) {
      patients = patients.filter((p) =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    // Apply risk filter
    switch (filterOption) {
      case FILTER_OPTIONS.HIGH_RISK.key:
        patients = patients.filter((p) => p.risk > 0.7);
        break;
      case FILTER_OPTIONS.MEDIUM_RISK.key:
        patients = patients.filter((p) => p.risk >= 0.5 && p.risk <= 0.7);
        break;
      case FILTER_OPTIONS.LOW_RISK.key:
        patients = patients.filter((p) => p.risk < 0.5);
        break;
      case FILTER_OPTIONS.ALL.key:
      default:
        break;
    }

    // Apply sort
    switch (sortOption) {
      case SORT_OPTIONS.NAME_ASC.key:
        patients.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case SORT_OPTIONS.NAME_DESC.key:
        patients.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case SORT_OPTIONS.RISK_ASC.key:
        patients.sort((a, b) => a.risk - b.risk);
        break;
      case SORT_OPTIONS.RISK_DESC.key:
        patients.sort((a, b) => b.risk - a.risk);
        break;
      case SORT_OPTIONS.UPDATE_DESC.key:
        patients.sort(
          (a, b) => new Date(b.last_update) - new Date(a.last_update),
        );
        break;
      default:
        break;
    }

    return patients;
  }, [allPatients, searchTerm, filterOption, sortOption]);

  const renderPatient = ({ item }) => (
    <TouchableOpacity
      onPress={() =>
        navigation.navigate("PatientDetail", {
          patientId: item.id,
          patientName: item.name,
        })
      }
      testID={`patient-item-${item.id}`}
    >
      <Card style={styles.patientCard}>
        <View style={styles.patientInfo}>
          <Text style={styles.patientName}>{item.name}</Text>
          <Text style={styles.patientDetails}>
            Age: {item.age} | Last Update: {item.last_update}
          </Text>
        </View>
        <View style={styles.riskContainer}>
          <Text style={[styles.riskScore, { color: getRiskColor(item.risk) }]}>
            {`${(item.risk * 100).toFixed(0)}%`}
          </Text>
          <Text style={styles.riskLabel}>Risk</Text>
        </View>
      </Card>
    </TouchableOpacity>
  );

  const renderOptionModal = (
    isVisible,
    setVisible,
    options,
    currentOption,
    setOption,
    title,
  ) => (
    <Modal
      animationType="fade"
      transparent={true}
      visible={isVisible}
      onRequestClose={() => setVisible(false)}
    >
      <Pressable style={styles.modalOverlay} onPress={() => setVisible(false)}>
        <Pressable
          style={styles.modalContent}
          onPress={(e) => e.stopPropagation()}
        >
          <Text style={styles.modalTitle}>{title}</Text>
          {Object.values(options).map((opt) => (
            <TouchableOpacity
              key={opt.key}
              style={styles.modalOption}
              onPress={() => {
                setOption(opt.key);
                setVisible(false);
              }}
            >
              <Text
                style={[
                  styles.modalOptionText,
                  currentOption === opt.key && styles.modalOptionSelected,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
          <CustomButton
            title="Close"
            onPress={() => setVisible(false)}
            style={styles.modalCloseButton}
          />
        </Pressable>
      </Pressable>
    </Modal>
  );

  if (loading && !allPatients.length) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper testID="patient-list-tab">
      {renderOptionModal(
        isSortModalVisible,
        setSortModalVisible,
        SORT_OPTIONS,
        sortOption,
        setSortOption,
        "Sort Patients By",
      )}
      {renderOptionModal(
        isFilterModalVisible,
        setFilterModalVisible,
        FILTER_OPTIONS,
        filterOption,
        setFilterOption,
        "Filter Patients By Risk",
      )}

      <View style={styles.header}>
        <Text style={styles.welcomeText}>Welcome, {username}!</Text>
        <CustomButton
          title="Logout"
          onPress={handleLogout}
          style={styles.logoutButton}
          textStyle={styles.logoutButtonText}
        />
      </View>

      {error && (
        <View style={styles.errorContainer} testID="error-message">
          <Text style={styles.errorText}>{error}</Text>
          <CustomButton
            title="Retry"
            onPress={() => loadData()}
            style={styles.retryButton}
            testID="retry-button"
          />
        </View>
      )}

      <View style={styles.controlsContainer}>
        <CustomInput
          placeholder="Search patients by name..."
          value={searchTerm}
          onChangeText={setSearchTerm}
          style={styles.searchInput}
          testID="search-input"
        />
        <View style={styles.buttonRow}>
          <CustomButton
            title={`Sort: ${SORT_OPTIONS[Object.keys(SORT_OPTIONS).find((key) => SORT_OPTIONS[key].key === sortOption)].label}`}
            onPress={() => setSortModalVisible(true)}
            style={styles.controlButton}
            textStyle={styles.controlButtonText}
          />
          <CustomButton
            title={`Filter: ${FILTER_OPTIONS[Object.keys(FILTER_OPTIONS).find((key) => FILTER_OPTIONS[key].key === filterOption)].label}`}
            onPress={() => setFilterModalVisible(true)}
            style={styles.controlButton}
            textStyle={styles.controlButtonText}
          />
        </View>
      </View>

      <FlatList
        data={filteredAndSortedPatients}
        renderItem={renderPatient}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={
          <Text style={styles.listTitle}>Patient Risk Overview</Text>
        }
        ListEmptyComponent={
          <Text style={styles.emptyListText}>
            No patients match your criteria.
          </Text>
        }
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[Colors.primary]}
            tintColor={Colors.primary}
          />
        }
        testID="patient-list"
      />
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.sm,
  },
  welcomeText: {
    ...Typography.h4,
    color: Colors.text,
  },
  logoutButton: {
    backgroundColor: Colors.error,
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    minHeight: 30,
  },
  logoutButtonText: {
    ...Typography.caption,
    fontWeight: "bold",
    color: Colors.surface,
  },
  errorContainer: {
    backgroundColor: Colors.error,
    padding: Spacing.md,
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.md,
    borderRadius: 8,
  },
  errorText: {
    ...Typography.body2,
    color: Colors.surface,
    marginBottom: Spacing.sm,
  },
  retryButton: {
    backgroundColor: Colors.surface,
  },
  controlsContainer: {
    paddingHorizontal: Spacing.md,
    marginBottom: Spacing.md,
  },
  searchInput: {
    marginBottom: Spacing.sm,
  },
  buttonRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  controlButton: {
    flex: 1,
    marginHorizontal: Spacing.xs,
    backgroundColor: Colors.secondary,
    paddingVertical: Spacing.sm,
  },
  controlButtonText: {
    ...Typography.caption,
    fontWeight: "600",
  },
  listContainer: {
    paddingBottom: Spacing.md,
  },
  listTitle: {
    ...Typography.h3,
    color: Colors.text,
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.md,
  },
  patientCard: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginHorizontal: Spacing.md,
  },
  patientInfo: {
    flex: 1,
    marginRight: Spacing.sm,
  },
  patientName: {
    ...Typography.body1,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  patientDetails: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
  riskContainer: {
    alignItems: "center",
  },
  riskScore: {
    ...Typography.h3,
    fontWeight: "bold",
  },
  riskLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: -Spacing.xs,
  },
  emptyListText: {
    ...Typography.body1,
    color: Colors.textSecondary,
    textAlign: "center",
    marginTop: Spacing.xxl,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalContent: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.lg,
    width: "85%",
    maxHeight: "70%",
    elevation: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  modalTitle: {
    ...Typography.h4,
    marginBottom: Spacing.md,
    textAlign: "center",
    color: Colors.primary,
  },
  modalOption: {
    paddingVertical: Spacing.sm + 2,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalOptionText: {
    ...Typography.body1,
    textAlign: "center",
    color: Colors.text,
  },
  modalOptionSelected: {
    fontWeight: "bold",
    color: Colors.primary,
  },
  modalCloseButton: {
    marginTop: Spacing.md,
    backgroundColor: Colors.textSecondary,
  },
});

export default HomeScreen;
