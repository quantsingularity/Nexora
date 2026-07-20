import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Card from "../components/Card";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import ScreenWrapper from "../components/ScreenWrapper";
import api from "../services/api";
import {
  Colors,
  GlobalStyles,
  Radius,
  Spacing,
  Typography,
} from "../theme/theme";

const MODEL_DESCRIPTIONS = {
  deep_fm: "Factorization-machine deep network for 30-day readmission risk.",
  survival_analysis:
    "Time-to-event model estimating readmission likelihood over time.",
  transformer_model:
    "Sequence transformer for longitudinal clinical event patterns.",
};

const PredictionModelsScreen = () => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [patientId, setPatientId] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [runError, setRunError] = useState("");

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getModels();
      setModels(data);
      setSelectedModel((prev) => prev || data[0] || null);
    } catch (err) {
      setError(err.message || "Failed to load models.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRun = async () => {
    if (!selectedModel || !patientId.trim()) {
      setRunError("Enter a patient ID to run a prediction.");
      return;
    }
    setRunning(true);
    setRunError("");
    setResult(null);
    try {
      const res = await api.makePrediction(selectedModel.name, undefined, {
        patient_id: patientId.trim(),
        demographics: {},
        clinical_events: [],
      });
      setResult(res);
    } catch (err) {
      setRunError(err.message || "Prediction failed.");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <ScreenWrapper style={GlobalStyles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper testID="models-screen">
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={styles.headerTitle}>Prediction Models</Text>
        <Text style={styles.headerSubtitle}>
          Registered in the ml_core model registry
        </Text>

        {error && <Text style={styles.errorText}>{error}</Text>}

        {models.map((model) => {
          const selected = selectedModel?.name === model.name;
          return (
            <TouchableOpacity
              key={model.name}
              onPress={() => setSelectedModel(model)}
            >
              <Card
                style={[styles.modelCard, selected && styles.modelCardSelected]}
              >
                <View style={styles.modelCardHeader}>
                  <View style={styles.modelIcon}>
                    <MaterialCommunityIcons
                      name="brain"
                      size={20}
                      color={Colors.primary}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.modelName}>{model.displayName}</Text>
                    <Text style={styles.modelVersion}>
                      Version {model.version}
                    </Text>
                  </View>
                  <View style={styles.statusBadge}>
                    <Text style={styles.statusBadgeText}>{model.status}</Text>
                  </View>
                </View>
                <Text style={styles.modelDescription}>
                  {MODEL_DESCRIPTIONS[model.name] ||
                    "Registered clinical prediction model."}
                </Text>
              </Card>
            </TouchableOpacity>
          );
        })}

        <Card>
          <Text style={styles.sectionTitle}>Run a Live Prediction</Text>
          <Text style={styles.sectionSubtitle}>
            Calls /predict using{" "}
            {selectedModel?.displayName || "the selected model"}
          </Text>
          <CustomInput
            label="Patient ID"
            placeholder="e.g. P00001"
            value={patientId}
            onChangeText={setPatientId}
            autoCapitalize="characters"
          />
          <CustomButton
            title={running ? "Running…" : "Run Prediction"}
            onPress={handleRun}
            loading={running}
            disabled={!selectedModel}
          />
          {runError ? <Text style={styles.errorText}>{runError}</Text> : null}

          {result && (
            <View style={styles.resultBox}>
              <Text style={styles.resultLabel}>Risk Score</Text>
              <Text style={styles.resultValue}>
                {(
                  (result.predictions?.risk_score ??
                    result.predictions?.risk ??
                    0) * 100
                ).toFixed(1)}
                %
              </Text>
              {!!(result.predictions?.top_features || []).length && (
                <>
                  <Text style={styles.resultLabel}>Top Features</Text>
                  <Text style={styles.resultFeatures}>
                    {(result.predictions.top_features || []).join(", ")}
                  </Text>
                </>
              )}
              <Text style={styles.resultMeta}>
                {result.model_name} {result.model_version} · {result.request_id}
              </Text>
            </View>
          )}
        </Card>

        <View style={{ height: Spacing.xl }} />
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  headerTitle: { ...Typography.h3, color: Colors.text, marginBottom: 2 },
  headerSubtitle: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  modelCard: { borderWidth: 1.5, borderColor: "transparent" },
  modelCardSelected: { borderColor: Colors.primary },
  modelCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: Spacing.sm,
  },
  modelIcon: {
    width: 36,
    height: 36,
    borderRadius: Radius.sm,
    backgroundColor: "rgba(37, 99, 235, 0.1)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: Spacing.sm,
  },
  modelName: { ...Typography.body1, fontWeight: "700", color: Colors.text },
  modelVersion: { ...Typography.caption, color: Colors.textSecondary },
  statusBadge: {
    backgroundColor: "rgba(22, 163, 74, 0.12)",
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: 999,
  },
  statusBadgeText: {
    ...Typography.caption,
    color: Colors.success,
    fontWeight: "700",
  },
  modelDescription: { ...Typography.body2, color: Colors.textSecondary },
  sectionTitle: { ...Typography.h4, color: Colors.text },
  sectionSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  errorText: {
    ...Typography.body2,
    color: Colors.error,
    marginTop: Spacing.xs,
    marginBottom: Spacing.xs,
  },
  resultBox: {
    marginTop: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: Colors.surfaceAlt,
  },
  resultLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  resultValue: { ...Typography.h2, color: Colors.primary },
  resultFeatures: { ...Typography.body2, color: Colors.text },
  resultMeta: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
  },
});

export default PredictionModelsScreen;
