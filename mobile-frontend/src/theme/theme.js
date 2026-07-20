// ── Nexora design system (mobile) ───────────────────────────────────────
// Mirrors web-frontend/src/assets/styles/theme.js so both apps share one
// brand identity: brand blue for navigation/primary actions, clinical teal
// for accents, and shared risk colors (Low/Medium/High).
// ─────────────────────────────────────────────────────────────────────────

export const Colors = {
  primary: "#2563EB", // brand blue
  primaryDark: "#1E3A8A",
  primaryLight: "#60A5FA",
  secondary: "#0D9488", // clinical teal
  secondaryDark: "#115E59",
  secondaryLight: "#2DD4BF",
  accent: "#0D9488",

  background: "#F8FAFC",
  surface: "#FFFFFF",
  surfaceAlt: "#F1F5F9",

  text: "#0F172A",
  textSecondary: "#64748B",

  error: "#DC2626", // also "High risk"
  warning: "#D97706", // also "Medium risk"
  success: "#16A34A", // also "Low risk"
  info: "#0EA5E9",

  border: "#E2E8F0",
  disabled: "#CBD5E1",
};

// Gradient stops for <LinearGradient> (expo-linear-gradient); matches the
// web hero gradient (brand.gradient in theme.js).
export const GradientColors = ["#1E3A8A", "#2563EB", "#0D9488"];

export const Typography = {
  h1: { fontSize: 34, fontWeight: "800" },
  h2: { fontSize: 28, fontWeight: "800" },
  h3: { fontSize: 22, fontWeight: "700" },
  h4: { fontSize: 20, fontWeight: "700" },
  body1: { fontSize: 17, fontWeight: "400" },
  body2: { fontSize: 15, fontWeight: "400" },
  caption: { fontSize: 13, fontWeight: "400" },
  button: { fontSize: 17, fontWeight: "600" },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const Radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 999,
};

export const GlobalStyles = {
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    padding: Spacing.md,
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: Colors.background,
  },
};

// Shared helpers so every screen renders risk consistently.
export const getRiskColor = (risk) => {
  if (risk === undefined || risk === null) return Colors.textSecondary;
  if (risk >= 0.75) return Colors.error;
  if (risk >= 0.4) return Colors.warning;
  return Colors.success;
};

export const getRiskLabel = (risk) => {
  if (risk === undefined || risk === null) return "Unknown";
  if (risk >= 0.75) return "High";
  if (risk >= 0.4) return "Medium";
  return "Low";
};
