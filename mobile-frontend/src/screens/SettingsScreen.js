import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useEffect, useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, View } from "react-native";
import Card from "../components/Card";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import ScreenWrapper from "../components/ScreenWrapper";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import { Colors, Spacing, Typography } from "../theme/theme";

const SettingsScreen = () => {
  const { user, refreshUser, logout } = useAuth();

  const [profileForm, setProfileForm] = useState({
    fullName: "",
    organization: "",
    specialty: "",
  });
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileForm({
        fullName: user.full_name || "",
        organization: user.organization || "",
        specialty: user.specialty || "",
      });
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      await api.updateProfile(profileForm);
      await refreshUser();
      Alert.alert("Saved", "Your profile was updated.");
    } catch (err) {
      Alert.alert("Error", err.message || "Failed to update profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  const [pwForm, setPwForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [savingPassword, setSavingPassword] = useState(false);

  const handleChangePassword = async () => {
    if (pwForm.newPassword !== pwForm.confirmPassword) {
      Alert.alert("Error", "New passwords do not match.");
      return;
    }
    if (pwForm.newPassword.length < 8) {
      Alert.alert("Error", "New password must be at least 8 characters.");
      return;
    }
    setSavingPassword(true);
    try {
      await api.changePassword({
        currentPassword: pwForm.currentPassword,
        newPassword: pwForm.newPassword,
      });
      setPwForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      Alert.alert("Saved", "Your password was changed.");
    } catch (err) {
      Alert.alert("Error", err.message || "Failed to change password.");
    } finally {
      setSavingPassword(false);
    }
  };

  const [health, setHealth] = useState(null);
  const [checkingHealth, setCheckingHealth] = useState(false);

  const checkHealth = async () => {
    setCheckingHealth(true);
    try {
      const result = await api.checkHealth();
      setHealth({ ok: true, ...result });
    } catch (err) {
      setHealth({ ok: false, message: err.message });
    } finally {
      setCheckingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleLogout = () => {
    Alert.alert("Sign Out", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      { text: "Sign Out", style: "destructive", onPress: logout },
    ]);
  };

  return (
    <ScreenWrapper testID="settings-screen">
      <ScrollView
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.headerTitle}>Settings</Text>

        <Card>
          <Text style={styles.sectionTitle}>Profile</Text>
          <CustomInput
            label="Full Name"
            value={profileForm.fullName}
            onChangeText={(v) => setProfileForm((f) => ({ ...f, fullName: v }))}
          />
          <CustomInput
            label="Email"
            value={user?.email || ""}
            editable={false}
          />
          <CustomInput
            label="Organization"
            value={profileForm.organization}
            onChangeText={(v) =>
              setProfileForm((f) => ({ ...f, organization: v }))
            }
          />
          <CustomInput
            label="Specialty"
            value={profileForm.specialty}
            onChangeText={(v) =>
              setProfileForm((f) => ({ ...f, specialty: v }))
            }
          />
          <CustomButton
            title={savingProfile ? "Saving…" : "Save Profile"}
            onPress={handleSaveProfile}
            loading={savingProfile}
          />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>Security</Text>
          <CustomInput
            label="Current Password"
            value={pwForm.currentPassword}
            onChangeText={(v) =>
              setPwForm((f) => ({ ...f, currentPassword: v }))
            }
            secureTextEntry
          />
          <CustomInput
            label="New Password"
            value={pwForm.newPassword}
            onChangeText={(v) => setPwForm((f) => ({ ...f, newPassword: v }))}
            secureTextEntry
          />
          <CustomInput
            label="Confirm New Password"
            value={pwForm.confirmPassword}
            onChangeText={(v) =>
              setPwForm((f) => ({ ...f, confirmPassword: v }))
            }
            secureTextEntry
          />
          <CustomButton
            title={savingPassword ? "Updating…" : "Update Password"}
            onPress={handleChangePassword}
            loading={savingPassword}
          />
        </Card>

        <Card>
          <View style={styles.systemHeader}>
            <Text style={styles.sectionTitle}>System</Text>
            <CustomButton
              title={checkingHealth ? "Checking…" : "Check"}
              onPress={checkHealth}
              style={styles.checkButton}
              textStyle={styles.checkButtonText}
            />
          </View>
          {health && (
            <View style={styles.healthRow}>
              <MaterialCommunityIcons
                name={health.ok ? "check-circle" : "close-circle"}
                size={18}
                color={health.ok ? Colors.success : Colors.error}
              />
              <Text style={styles.healthText}>
                {health.ok
                  ? `Backend is ${health.status} (v${health.version})`
                  : health.message}
              </Text>
            </View>
          )}
          <Text style={styles.metaText}>API: {api.getBaseURL()}</Text>
          <Text style={styles.metaText}>Nexora Mobile v1.0.0</Text>
        </Card>

        <CustomButton
          title="Sign Out"
          onPress={handleLogout}
          style={styles.logoutButton}
        />

        <View style={{ height: Spacing.xl }} />
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  headerTitle: {
    ...Typography.h3,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  systemHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  checkButton: {
    paddingVertical: 6,
    paddingHorizontal: Spacing.sm,
    minHeight: 32,
  },
  checkButtonText: { fontSize: 13 },
  healthRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: Spacing.xs,
  },
  healthText: {
    ...Typography.body2,
    color: Colors.text,
    marginLeft: Spacing.xs,
    flex: 1,
  },
  metaText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
  },
  logoutButton: { backgroundColor: Colors.error, marginTop: Spacing.sm },
});

export default SettingsScreen;
