import { MaterialCommunityIcons } from "@expo/vector-icons";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import { ActivityIndicator, View } from "react-native";
import { useAuth } from "../context/AuthContext";
import AlertsScreen from "../screens/AlertsScreen";
import DashboardScreen from "../screens/DashboardScreen";
import HomepageScreen from "../screens/HomepageScreen";
import LoginScreen from "../screens/LoginScreen";
import PatientDetailScreen from "../screens/PatientDetailScreen";
import PatientListScreen from "../screens/PatientListScreen";
import PredictionModelsScreen from "../screens/PredictionModelsScreen";
import SettingsScreen from "../screens/SettingsScreen";
import SignUpScreen from "../screens/SignUpScreen";
import { Colors } from "../theme/theme";

const RootStack = createStackNavigator();
const AuthStack = createStackNavigator();
const PatientsStack = createStackNavigator();
const Tab = createBottomTabNavigator();

// ── Auth flow: Login <-> SignUp ──────────────────────────────────────────
const AuthNavigator = () => (
  <AuthStack.Navigator
    initialRouteName="Login"
    screenOptions={{ headerShown: false }}
  >
    <AuthStack.Screen name="Login" component={LoginScreen} />
    <AuthStack.Screen name="SignUp" component={SignUpScreen} />
  </AuthStack.Navigator>
);

// ── Patients tab: list -> detail ─────────────────────────────────────────
const PatientsNavigator = () => (
  <PatientsStack.Navigator
    screenOptions={{
      headerStyle: {
        backgroundColor: Colors.surface,
        elevation: 1,
        shadowOpacity: 0.06,
      },
      headerTintColor: Colors.text,
      headerTitleStyle: { fontWeight: "700" },
    }}
  >
    <PatientsStack.Screen
      name="PatientList"
      component={PatientListScreen}
      options={{ title: "Patients", headerShown: false }}
    />
    <PatientsStack.Screen
      name="PatientDetail"
      component={PatientDetailScreen}
      options={{ title: "Patient" }}
    />
  </PatientsStack.Navigator>
);

// ── Main app: bottom tabs ─────────────────────────────────────────────────
const TAB_ICONS = {
  DashboardTab: "view-dashboard-outline",
  PatientsTab: "account-group-outline",
  ModelsTab: "brain",
  AlertsTab: "bell-outline",
  SettingsTab: "cog-outline",
};

const MainTabNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      headerShown: route.name !== "PatientsTab",
      headerStyle: {
        backgroundColor: Colors.surface,
        elevation: 1,
        shadowOpacity: 0.06,
      },
      headerTitleStyle: { fontWeight: "700" },
      tabBarActiveTintColor: Colors.primary,
      tabBarInactiveTintColor: Colors.textSecondary,
      tabBarStyle: { borderTopColor: Colors.border },
      tabBarIcon: ({ color, size }) => (
        <MaterialCommunityIcons
          name={TAB_ICONS[route.name]}
          color={color}
          size={size}
        />
      ),
    })}
  >
    <Tab.Screen
      name="DashboardTab"
      component={DashboardScreen}
      options={{ title: "Dashboard" }}
    />
    <Tab.Screen
      name="PatientsTab"
      component={PatientsNavigator}
      options={{ title: "Patients" }}
    />
    <Tab.Screen
      name="ModelsTab"
      component={PredictionModelsScreen}
      options={{ title: "Models" }}
    />
    <Tab.Screen
      name="AlertsTab"
      component={AlertsScreen}
      options={{ title: "Alerts" }}
    />
    <Tab.Screen
      name="SettingsTab"
      component={SettingsScreen}
      options={{ title: "Settings" }}
    />
  </Tab.Navigator>
);

// ── Root: Homepage (public) OR Main (signed in) ──────────────────────────
const SplashLoader = () => (
  <View
    style={{
      flex: 1,
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: Colors.background,
    }}
  >
    <ActivityIndicator size="large" color={Colors.primary} />
  </View>
);

const AppNavigator = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <SplashLoader />;

  return (
    <RootStack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <RootStack.Screen name="Main" component={MainTabNavigator} />
      ) : (
        <>
          <RootStack.Screen name="Homepage" component={HomepageScreen} />
          <RootStack.Screen name="Auth" component={AuthNavigator} />
        </>
      )}
    </RootStack.Navigator>
  );
};

export default AppNavigator;
