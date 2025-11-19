import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Colors, Typography, Spacing, GlobalStyles } from '../theme/theme';
import CustomButton from '../components/CustomButton';
import CustomInput from '../components/CustomInput';
import ScreenWrapper from '../components/ScreenWrapper';

const LoginScreen = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const validateInput = () => {
    let isValid = true;
    setUsernameError('');
    setPasswordError('');

    if (!username.trim()) {
      setUsernameError('Username is required.');
      isValid = false;
    }
    if (!password.trim()) {
      setPasswordError('Password is required.');
      isValid = false;
    }
    return isValid;
  };

  const handleLogin = async () => {
    if (!validateInput()) {
      return;
    }

    setLoading(true);
    // Mock authentication - replace with actual API call
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    if (username === 'clinician' && password === 'password123') {
      try {
        await AsyncStorage.setItem('userToken', 'mock-token');
        await AsyncStorage.setItem('username', username);
        navigation.replace('Home'); // Use replace to prevent going back to Login
      } catch (e) {
        Alert.alert('Login Failed', 'Could not save user session. Please try again.');
      } finally {
        setLoading(false);
      }
    } else {
      Alert.alert('Login Failed', 'Invalid username or password.');
      setLoading(false);
    }
  };

  return (
    <ScreenWrapper style={styles.container} useSafeArea={true}>
      <View style={styles.logoContainer}>
        {/* Placeholder for Logo - Add your logo image here */}
        {/* <Image source={require('../assets/logo.png')} style={styles.logo} /> */}
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
          keyboardType="email-address" // Assuming username might be email
          error={usernameError}
        />
        <CustomInput
          label="Password"
          placeholder="Enter your password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          error={passwordError}
        />
        <CustomButton
          title="Login"
          onPress={handleLogin}
          loading={loading}
          style={styles.loginButton}
        />
      </View>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    paddingHorizontal: Spacing.lg, // More padding
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: Spacing.xxl,
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: Spacing.md,
    // Add styles for your logo
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
    width: '100%',
  },
  loginButton: {
    marginTop: Spacing.md,
  },
});

export default LoginScreen;
