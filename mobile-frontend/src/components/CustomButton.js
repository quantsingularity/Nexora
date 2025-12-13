import React from "react";
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { Colors, Typography, Spacing } from "../theme/theme";

const CustomButton = ({
  title,
  onPress,
  style,
  textStyle,
  disabled,
  loading,
  testID,
  ...props
}) => {
  return (
    <TouchableOpacity
      style={[styles.button, disabled || loading ? styles.disabled : {}, style]}
      onPress={onPress}
      disabled={disabled || loading}
      testID={testID}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={Colors.surface} />
      ) : (
        <Text style={[styles.text, textStyle]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    backgroundColor: Colors.primary,
    paddingVertical: Spacing.sm + 4,
    paddingHorizontal: Spacing.md,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 44,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.5,
  },
  text: {
    ...Typography.button,
    color: Colors.surface,
  },
  disabled: {
    backgroundColor: Colors.disabled,
    elevation: 0,
    shadowOpacity: 0,
  },
});

export default CustomButton;
