import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import ScreenWrapper from "../components/ScreenWrapper";
import { useAuth } from "../context/AuthContext";
import { Colors, Spacing, Typography } from "../theme/theme";

const SignUpScreen = ({ navigation }) => {
  const { register } = useAuth();
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    organization: "",
    specialty: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const setField = (field) => (value) =>
    setForm((f) => ({ ...f, [field]: value }));

  const validate = () => {
    const next = {};
    if (!form.fullName.trim()) next.fullName = "Full name is required.";
    if (!form.email.trim()) next.email = "Email is required.";
    if (!form.password) {
      next.password = "Password is required.";
    } else if (form.password.length < 8) {
      next.password = "Must be at least 8 characters.";
    } else if (!/\d/.test(form.password) || !/[a-zA-Z]/.test(form.password)) {
      next.password = "Needs at least one letter and one number.";
    }
    if (form.confirmPassword !== form.password) {
      next.confirmPassword = "Passwords do not match.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSignUp = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      await register({
        fullName: form.fullName.trim(),
        email: form.email.trim(),
        password: form.password,
        organization: form.organization.trim() || undefined,
        specialty: form.specialty.trim() || undefined,
      });
      // AppNavigator swaps to Main automatically once authenticated.
    } catch (error) {
      Alert.alert(
        "Sign Up Failed",
        error.message || "Unable to create your account. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenWrapper testID="signup-screen">
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <TouchableOpacity
          style={styles.backLink}
          onPress={() => navigation.goBack()}
        >
          <MaterialCommunityIcons
            name="arrow-left"
            size={20}
            color={Colors.textSecondary}
          />
          <Text style={styles.backLinkText}>Back</Text>
        </TouchableOpacity>

        <View style={styles.logoContainer}>
          <View style={styles.logoBadge}>
            <MaterialCommunityIcons
              name="hospital-box"
              size={28}
              color={Colors.surface}
            />
          </View>
          <Text style={styles.title}>Create your account</Text>
          <Text style={styles.subtitle}>Join Nexora as a clinician</Text>
        </View>

        <View style={styles.formContainer}>
          <CustomInput
            label="Full name"
            placeholder="Dr. Jane Rivera"
            value={form.fullName}
            onChangeText={setField("fullName")}
            error={errors.fullName}
          />
          <CustomInput
            label="Email address"
            placeholder="you@hospital.org"
            value={form.email}
            onChangeText={setField("email")}
            autoCapitalize="none"
            keyboardType="email-address"
            error={errors.email}
          />
          <CustomInput
            label="Organization (optional)"
            placeholder="Springfield General Hospital"
            value={form.organization}
            onChangeText={setField("organization")}
          />
          <CustomInput
            label="Specialty (optional)"
            placeholder="Internal Medicine"
            value={form.specialty}
            onChangeText={setField("specialty")}
          />
          <CustomInput
            label="Password"
            placeholder="At least 8 characters"
            value={form.password}
            onChangeText={setField("password")}
            secureTextEntry
            error={errors.password}
          />
          <CustomInput
            label="Confirm password"
            placeholder="Re-enter your password"
            value={form.confirmPassword}
            onChangeText={setField("confirmPassword")}
            secureTextEntry
            error={errors.confirmPassword}
          />

          <CustomButton
            title={loading ? "Creating account…" : "Create Account"}
            onPress={handleSignUp}
            loading={loading}
            style={styles.submitButton}
          />

          <TouchableOpacity
            style={styles.loginLink}
            onPress={() => navigation.navigate("Login")}
          >
            <Text style={styles.loginLinkText}>
              Already have an account?{" "}
              <Text style={styles.loginLinkBold}>Sign in</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.xxl,
  },
  backLink: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: Spacing.sm,
    marginBottom: Spacing.md,
  },
  backLinkText: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginLeft: 4,
  },
  logoContainer: {
    alignItems: "center",
    marginBottom: Spacing.lg,
  },
  logoBadge: {
    width: 52,
    height: 52,
    borderRadius: 14,
    backgroundColor: Colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.sm,
  },
  title: {
    ...Typography.h3,
    color: Colors.text,
  },
  subtitle: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  formContainer: {
    width: "100%",
  },
  submitButton: {
    marginTop: Spacing.md,
  },
  loginLink: {
    marginTop: Spacing.lg,
    alignItems: "center",
  },
  loginLinkText: {
    ...Typography.body2,
    color: Colors.textSecondary,
  },
  loginLinkBold: {
    color: Colors.primary,
    fontWeight: "700",
  },
});

export default SignUpScreen;
