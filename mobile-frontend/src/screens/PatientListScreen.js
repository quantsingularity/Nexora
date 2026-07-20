import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Card from "../components/Card";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import { PatientCard } from "../components/PatientCard";
import ScreenWrapper from "../components/ScreenWrapper";
import api from "../services/api";
import { Colors, GlobalStyles, Spacing, Typography } from "../theme/theme";

const SORT_OPTIONS = {
  RISK_DESC: { label: "Risk (High-Low)", key: "risk_desc" },
  RISK_ASC: { label: "Risk (Low-High)", key: "risk_asc" },
  NAME_ASC: { label: "Name (A-Z)", key: "name_asc" },
  NAME_DESC: { label: "Name (Z-A)", key: "name_desc" },
};

const FILTER_OPTIONS = {
  ALL: { label: "All Patients", key: "all" },
  HIGH_RISK: { label: "High Risk (\u2265 75%)", key: "high" },
  MEDIUM_RISK: { label: "Medium Risk (40-74%)", key: "medium" },
  LOW_RISK: { label: "Low Risk (< 40%)", key: "low" },
};

const emptyForm = { name: "", age: "", gender: "Female", diagnosis: "" };

const PatientListScreen = ({ navigation, route }) => {
  const [allPatients, setAllPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortOption, setSortOption] = useState(SORT_OPTIONS.RISK_DESC.key);
  const [filterOption, setFilterOption] = useState(
    route?.params?.risk &&
      FILTER_OPTIONS[route.params.risk.toUpperCase() + "_RISK"]
      ? route.params.risk
      : FILTER_OPTIONS.ALL.key,
  );
  const [isSortModalVisible, setSortModalVisible] = useState(false);
  const [isFilterModalVisible, setFilterModalVisible] = useState(false);
  const [isAddModalVisible, setAddModalVisible] = useState(false);
  const [addForm, setAddForm] = useState(emptyForm);
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState("");
  const [error, setError] = useState(null);

  const loadData = async (isRefreshing = false) => {
    try {
      if (!isRefreshing) setLoading(true);
      setError(null);
      const patients = await api.getPatients();
      setAllPatients(patients);
    } catch (err) {
      setError(err.message || "Failed to load patients. Please try again.");
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

  const filteredAndSortedPatients = useMemo(() => {
    let patients = [...allPatients];

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      patients = patients.filter(
        (p) =>
          p.name.toLowerCase().includes(q) || p.id.toLowerCase().includes(q),
      );
    }

    switch (filterOption) {
      case "high":
        patients = patients.filter((p) => p.riskScore >= 0.75);
        break;
      case "medium":
        patients = patients.filter(
          (p) => p.riskScore >= 0.4 && p.riskScore < 0.75,
        );
        break;
      case "low":
        patients = patients.filter((p) => p.riskScore < 0.4);
        break;
      default:
        break;
    }

    switch (sortOption) {
      case "name_asc":
        patients.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case "name_desc":
        patients.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case "risk_asc":
        patients.sort((a, b) => a.riskScore - b.riskScore);
        break;
      case "risk_desc":
      default:
        patients.sort((a, b) => b.riskScore - a.riskScore);
        break;
    }

    return patients;
  }, [allPatients, searchTerm, filterOption, sortOption]);

  const handleAddPatient = async () => {
    if (!addForm.name.trim()) {
      setAddError("Patient name is required.");
      return;
    }
    setAddSubmitting(true);
    setAddError("");
    try {
      await api.addPatient({
        name: addForm.name.trim(),
        age: addForm.age ? Number(addForm.age) : undefined,
        gender: addForm.gender || undefined,
        diagnosis: addForm.diagnosis.trim() || undefined,
      });
      setAddModalVisible(false);
      setAddForm(emptyForm);
      loadData();
    } catch (err) {
      setAddError(err.message || "Failed to add patient.");
    } finally {
      setAddSubmitting(false);
    }
  };

  const renderPatient = ({ item }) => (
    <PatientCard
      patient={{
        name: item.name,
        mrn: item.mrn,
        age: item.age,
        risk: item.riskScore,
        lastUpdated: item.lastVisit,
      }}
      onPress={() =>
        navigation.navigate("PatientDetail", {
          patientId: item.id,
          patientName: item.name,
        })
      }
      testID={`patient-item-${item.id}`}
    />
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
      transparent
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

      {/* Add Patient modal */}
      <Modal
        animationType="slide"
        transparent
        visible={isAddModalVisible}
        onRequestClose={() => setAddModalVisible(false)}
      >
        <Pressable
          style={styles.modalOverlay}
          onPress={() => setAddModalVisible(false)}
        >
          <Pressable
            style={styles.addModalContent}
            onPress={(e) => e.stopPropagation()}
          >
            <ScrollView keyboardShouldPersistTaps="handled">
              <Text style={styles.modalTitle}>Add New Patient</Text>
              {addError ? (
                <Text style={styles.formError}>{addError}</Text>
              ) : null}
              <CustomInput
                label="Full Name"
                value={addForm.name}
                onChangeText={(v) => setAddForm((f) => ({ ...f, name: v }))}
                placeholder="Jane Doe"
              />
              <CustomInput
                label="Age"
                value={addForm.age}
                onChangeText={(v) => setAddForm((f) => ({ ...f, age: v }))}
                keyboardType="number-pad"
                placeholder="58"
              />
              <CustomInput
                label="Gender"
                value={addForm.gender}
                onChangeText={(v) => setAddForm((f) => ({ ...f, gender: v }))}
                placeholder="Female / Male / Other"
              />
              <CustomInput
                label="Primary Diagnosis"
                value={addForm.diagnosis}
                onChangeText={(v) =>
                  setAddForm((f) => ({ ...f, diagnosis: v }))
                }
                placeholder="Type 2 Diabetes"
              />
              <Text style={styles.formHint}>
                A readmission risk score is computed automatically from the
                deep_fm model.
              </Text>
              <CustomButton
                title={addSubmitting ? "Adding…" : "Add Patient"}
                onPress={handleAddPatient}
                loading={addSubmitting}
                style={{ marginTop: Spacing.sm }}
              />
              <CustomButton
                title="Cancel"
                onPress={() => setAddModalVisible(false)}
                style={styles.modalCloseButton}
              />
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      <View style={styles.header}>
        <Text style={styles.headerTitle}>Patients</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setAddModalVisible(true)}
        >
          <MaterialCommunityIcons
            name="plus"
            size={22}
            color={Colors.surface}
          />
        </TouchableOpacity>
      </View>

      {error && (
        <Card style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <CustomButton
            title="Retry"
            onPress={() => loadData()}
            testID="retry-button"
          />
        </Card>
      )}

      <View style={styles.controlsContainer}>
        <CustomInput
          placeholder="Search patients by name or ID..."
          value={searchTerm}
          onChangeText={setSearchTerm}
          style={styles.searchInput}
          testID="search-input"
        />
        <View style={styles.buttonRow}>
          <CustomButton
            title={`Sort: ${Object.values(SORT_OPTIONS).find((o) => o.key === sortOption).label}`}
            onPress={() => setSortModalVisible(true)}
            style={styles.controlButton}
            textStyle={styles.controlButtonText}
          />
          <CustomButton
            title={`Filter: ${Object.values(FILTER_OPTIONS).find((o) => o.key === filterOption).label}`}
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
  },
  headerTitle: { ...Typography.h3, color: Colors.text },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  errorContainer: { backgroundColor: "#FEF2F2" },
  errorText: {
    ...Typography.body2,
    color: Colors.error,
    marginBottom: Spacing.sm,
  },
  controlsContainer: { marginBottom: Spacing.sm },
  searchInput: { marginBottom: Spacing.sm },
  buttonRow: { flexDirection: "row", justifyContent: "space-between" },
  controlButton: {
    flex: 1,
    marginHorizontal: Spacing.xs,
    backgroundColor: Colors.secondary,
    paddingVertical: Spacing.sm,
  },
  controlButtonText: { ...Typography.caption, fontWeight: "600" },
  listContainer: { paddingBottom: Spacing.xl },
  emptyListText: {
    ...Typography.body1,
    color: Colors.textSecondary,
    textAlign: "center",
    marginTop: Spacing.xxl,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(15, 23, 42, 0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalContent: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: Spacing.lg,
    width: "85%",
    maxHeight: "70%",
  },
  addModalContent: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: Spacing.lg,
    width: "90%",
    maxHeight: "85%",
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
  modalOptionSelected: { fontWeight: "bold", color: Colors.primary },
  modalCloseButton: {
    marginTop: Spacing.md,
    backgroundColor: Colors.textSecondary,
  },
  formError: {
    ...Typography.body2,
    color: Colors.error,
    marginBottom: Spacing.sm,
    textAlign: "center",
  },
  formHint: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
});

export default PatientListScreen;
