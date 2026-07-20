import { MaterialCommunityIcons } from "@expo/vector-icons";
import React from "react";
import { ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";
import CustomButton from "../components/CustomButton";
import { useAuth } from "../context/AuthContext";
import { Colors, Radius, Spacing, Typography } from "../theme/theme";

const FEATURES = [
  {
    icon: "chart-line",
    title: "Predictive Risk Scoring",
    description:
      "Deep-learning readmission risk scores for every patient, updated on demand.",
  },
  {
    icon: "account-group",
    title: "Patient Management",
    description: "A searchable, sortable roster of your full patient panel.",
  },
  {
    icon: "bell-alert-outline",
    title: "Real-Time Alerts",
    description: "Get notified the moment a patient crosses into high risk.",
  },
  {
    icon: "shield-check-outline",
    title: "HIPAA-Aware Auditing",
    description: "Every chart access is written to a compliance audit log.",
  },
];

const HomepageScreen = ({ navigation }) => {
  const { isAuthenticated } = useAuth();

  return (
    <View style={styles.root}>
      <StatusBar
        barStyle="light-content"
        backgroundColor={Colors.primaryDark}
      />
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Hero */}
        <View style={styles.hero}>
          <View style={styles.logoBadge}>
            <MaterialCommunityIcons
              name="hospital-box"
              size={34}
              color={Colors.surface}
            />
          </View>
          <Text style={styles.heroTitle}>NEXORA</Text>
          <Text style={styles.heroSubtitle}>Clinical Prediction System</Text>
          <Text style={styles.heroTagline}>
            AI-powered readmission risk prediction that helps care teams
            intervene before a patient ends up back in the hospital.
          </Text>

          <View style={styles.heroActions}>
            {isAuthenticated ? (
              <CustomButton
                title="Open Dashboard"
                onPress={() => navigation.replace("Main")}
                style={styles.primaryHeroButton}
              />
            ) : (
              <>
                <CustomButton
                  title="Get Started Free"
                  onPress={() =>
                    navigation.navigate("Auth", { screen: "SignUp" })
                  }
                  style={styles.primaryHeroButton}
                />
                <CustomButton
                  title="Sign In"
                  onPress={() =>
                    navigation.navigate("Auth", { screen: "Login" })
                  }
                  style={styles.secondaryHeroButton}
                  textStyle={styles.secondaryHeroButtonText}
                />
              </>
            )}
          </View>
        </View>

        {/* Feature grid */}
        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>Built for clinical teams</Text>
          {FEATURES.map((f) => (
            <View style={styles.featureRow} key={f.title}>
              <View style={styles.featureIcon}>
                <MaterialCommunityIcons
                  name={f.icon}
                  size={22}
                  color={Colors.primary}
                />
              </View>
              <View style={styles.featureText}>
                <Text style={styles.featureTitle}>{f.title}</Text>
                <Text style={styles.featureDescription}>{f.description}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Stats strip */}
        <View style={styles.statsStrip}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>3</Text>
            <Text style={styles.statLabel}>Prediction Models</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>24/7</Text>
            <Text style={styles.statLabel}>Live Scoring</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>HIPAA</Text>
            <Text style={styles.statLabel}>Audit Logging</Text>
          </View>
        </View>

        {/* Bottom CTA */}
        {!isAuthenticated && (
          <View style={styles.bottomCta}>
            <Text style={styles.bottomCtaTitle}>Ready to get started?</Text>
            <CustomButton
              title="Create Free Account"
              onPress={() => navigation.navigate("Auth", { screen: "SignUp" })}
              style={styles.primaryHeroButton}
            />
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  hero: {
    backgroundColor: Colors.primaryDark,
    paddingTop: Spacing.xxl + Spacing.lg,
    paddingBottom: Spacing.xl,
    paddingHorizontal: Spacing.lg,
    alignItems: "center",
  },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: Radius.lg,
    backgroundColor: "rgba(255,255,255,0.15)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.md,
  },
  heroTitle: {
    ...Typography.h1,
    color: Colors.surface,
    letterSpacing: 1,
  },
  heroSubtitle: {
    ...Typography.body1,
    color: "rgba(255,255,255,0.85)",
    marginTop: Spacing.xs,
  },
  heroTagline: {
    ...Typography.body2,
    color: "rgba(255,255,255,0.75)",
    textAlign: "center",
    marginTop: Spacing.md,
    lineHeight: 22,
  },
  heroActions: {
    width: "100%",
    marginTop: Spacing.xl,
    gap: Spacing.sm,
  },
  primaryHeroButton: {
    backgroundColor: Colors.surface,
  },
  secondaryHeroButton: {
    backgroundColor: "transparent",
    borderWidth: 1.5,
    borderColor: "rgba(255,255,255,0.6)",
  },
  secondaryHeroButtonText: {
    color: Colors.surface,
  },
  featuresSection: {
    padding: Spacing.lg,
  },
  sectionTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  featureRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: Spacing.lg,
  },
  featureIcon: {
    width: 44,
    height: 44,
    borderRadius: Radius.md,
    backgroundColor: "rgba(37, 99, 235, 0.1)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: Spacing.md,
  },
  featureText: { flex: 1 },
  featureTitle: {
    ...Typography.body1,
    fontWeight: "700",
    color: Colors.text,
  },
  featureDescription: {
    ...Typography.body2,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  statsStrip: {
    flexDirection: "row",
    backgroundColor: Colors.surface,
    marginHorizontal: Spacing.lg,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.xl,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  statItem: { flex: 1, alignItems: "center" },
  statDivider: { width: 1, backgroundColor: Colors.border },
  statValue: { ...Typography.h4, color: Colors.primary },
  statLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
    textAlign: "center",
  },
  bottomCta: {
    alignItems: "center",
    padding: Spacing.xl,
    paddingBottom: Spacing.xxl,
  },
  bottomCtaTitle: {
    ...Typography.h4,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
});

export default HomepageScreen;
