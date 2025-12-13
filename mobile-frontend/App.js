import React from "react";
import { View } from "react-native";
import AppNavigator from "./src/navigation/AppNavigator";
import { GestureHandlerRootView } from "react-native-gesture-handler";

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }} testID="app-container">
      <AppNavigator />
    </GestureHandlerRootView>
  );
}
