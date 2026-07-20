import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useState } from "react";
import { Alert, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import ScreenWrapper from "../components/ScreenWrapper";
import { useAuth } from "../context/AuthContext";
import { Colors, Spacing, Typography } from "../theme/theme";

const LoginScreen = ({ navigation }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [loading, setLoading] = useState(false);

  const validate = () => {
    let valid = true;
    setEmailError("");
    setPasswordError("");
    if (!email.trim()) {
      setEmailError("Email is required.");
      valid = false;
    }
    if (!password) {
      setPasswordError("Password is required.");
      valid = false;
    }
    return valid;
  };

  const handleLogin = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      await login({ email: email.trim(), password });
      // AppNavigator swaps to the Main tab navigator automatically once
      // isAuthenticated flips to true; no manual navigation needed here.
    } catch (error) {
      Alert.alert(
        "Sign In Failed",
        error.message || "Invalid email or password.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenWrapper style={styles.container} testID="login-screen">
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

      <View style={styles.logoContainer} testID="welcome">
        <View style={styles.logoBadge}>
          <MaterialCommunityIcons
            name="hospital-box"
            size={30}
            color={Colors.surface}
          />
        </View>
        <Text style={styles.title}>NEXORA</Text>
        <Text style={styles.subtitle}>Sign in to your account</Text>
      </View>

      <View style={styles.formContainer}>
        <CustomInput
          label="Email address"
          placeholder="you@hospital.org"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          error={emailError}
          testID="email-input"
        />
        <CustomInput
          label="Password"
          placeholder="Enter your password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          error={passwordError}
          testID="password-input"
        />
        <CustomButton
          title={loading ? "Signing in…" : "Sign In"}
          onPress={handleLogin}
          loading={loading}
          style={styles.loginButton}
          testID="login-button"
        />

        <TouchableOpacity
          style={styles.signupLink}
          onPress={() => navigation.navigate("SignUp")}
        >
          <Text style={styles.signupLinkText}>
            Need an account?{" "}
            <Text style={styles.signupLinkBold}>Create one</Text>
          </Text>
        </TouchableOpacity>
      </View>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: "center",
    paddingHorizontal: Spacing.lg,
  },
  backLink: {
    flexDirection: "row",
    alignItems: "center",
    position: "absolute",
    top: Spacing.md,
    left: Spacing.md,
  },
  backLinkText: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginLeft: 4,
  },
  logoContainer: {
    alignItems: "center",
    marginBottom: Spacing.xxl,
  },
  logoBadge: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: Colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.sm,
  },
  title: {
    ...Typography.h2,
    color: Colors.text,
    marginBottom: Spacing.xs,
    letterSpacing: 1,
  },
  subtitle: {
    ...Typography.body2,
    color: Colors.textSecondary,
  },
  formContainer: {
    width: "100%",
  },
  loginButton: {
    marginTop: Spacing.md,
  },
  signupLink: {
    marginTop: Spacing.lg,
    alignItems: "center",
  },
  signupLinkText: {
    ...Typography.body2,
    color: Colors.textSecondary,
  },
  signupLinkBold: {
    color: Colors.primary,
    fontWeight: "700",
  },
});

export default LoginScreen;
