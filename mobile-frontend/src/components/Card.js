import React from "react";
import { View, StyleSheet } from "react-native";
import { Colors, Spacing } from "../theme/theme";

const Card = ({ children, style, testID, ...props }) => {
  return (
    <View style={[styles.card, style]} testID={testID} {...props}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    // iOS Shadow
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    // Android Shadow
    elevation: 3,
  },
});

export default Card;
