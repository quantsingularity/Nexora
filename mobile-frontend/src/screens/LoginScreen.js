import React, { useState } from "react";
import { View, Text, StyleSheet, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Colors, Typography, Spacing } from "../theme/theme";
import CustomButton from "../components/CustomButton";
import CustomInput from "../components/CustomInput";
import ScreenWrapper from "../components/ScreenWrapper";
import apiService from "../services/api";

const LoginScreen = ({ navigation }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [usernameError, setUsernameError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const validateInput = () => {
    let isValid = true;
    setUsernameError("");
    setPasswordError("");

    if (!username.trim()) {
      setUsernameError("Username is required.");
      isValid = false;
    }
    if (!password.trim()) {
      setPasswordError("Password is required.");
      isValid = false;
    }
    return isValid;
  };

  const handleLogin = async () => {
    if (!validateInput()) {
      return;
    }

    setLoading(true);
    try {
      // Use the API service for authentication
      const response = await apiService.login(username, password);

      if (response.success || response.token) {
        await AsyncStorage.setItem("userToken", response.token);
        await AsyncStorage.setItem("username", username);
        navigation.replace("Home");
      } else {
        Alert.alert("Login Failed", "Invalid response from server.");
      }
    } catch (error) {
      console.error("Login error:", error);
      Alert.alert(
        "Login Failed",
        error.message || "Invalid username or password.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenWrapper
      style={styles.container}
      useSafeArea={true}
      testID="login-screen"
    >
      <View style={styles.logoContainer} testID="welcome">
        <Text style={styles.title}>Nexora Mobile</Text>
        <Text style={styles.subtitle}>Clinical Decision Support</Text>
      </View>

      <View style={styles.formContainer}>
        <CustomInput
          label="Username"
          placeholder="Enter your username"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          keyboardType="email-address"
          error={usernameError}
          testID="username-input"
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
          title="Login"
          onPress={handleLogin}
          loading={loading}
          style={styles.loginButton}
          testID="login-button"
        />
        <Text style={styles.hintText}>
          Demo credentials: clinician / password123
        </Text>
      </View>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: "center",
    paddingHorizontal: Spacing.lg,
  },
  logoContainer: {
    alignItems: "center",
    marginBottom: Spacing.xxl,
  },
  title: {
    ...Typography.h2,
    color: Colors.primary,
    marginBottom: Spacing.xs,
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
  hintText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    textAlign: "center",
    marginTop: Spacing.md,
  },
});

export default LoginScreen;
