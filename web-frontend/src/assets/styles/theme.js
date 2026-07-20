import { createTheme } from "@mui/material/styles";

// ── Nexora design system ────────────────────────────────────────────────
// This palette & type scale is mirrored in mobile-frontend/src/theme/theme.js
// so the web and mobile apps present the same brand identity.
//
//   primary  (brand blue)   → navigation, primary actions, links
//   secondary (clinical teal) → accents, secondary actions
//   success / warning / error → also used for Low / Medium / High risk chips
// ─────────────────────────────────────────────────────────────────────────

export const brand = {
  primary: "#2563EB",
  primaryDark: "#1E3A8A",
  primaryLight: "#60A5FA",
  secondary: "#0D9488",
  secondaryDark: "#115E59",
  secondaryLight: "#2DD4BF",
  riskHigh: "#DC2626",
  riskMedium: "#D97706",
  riskLow: "#16A34A",
  surface: "#F8FAFC",
  gradient: "linear-gradient(135deg, #1E3A8A 0%, #2563EB 55%, #0D9488 100%)",
};

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: brand.primary,
      light: brand.primaryLight,
      dark: brand.primaryDark,
      contrastText: "#ffffff",
    },
    secondary: {
      main: brand.secondary,
      light: brand.secondaryLight,
      dark: brand.secondaryDark,
      contrastText: "#ffffff",
    },
    background: {
      default: brand.surface,
      paper: "#ffffff",
    },
    text: {
      primary: "#0F172A",
      secondary: "#64748B",
    },
    success: { main: brand.riskLow, light: "#4ADE80", dark: "#15803D" },
    warning: { main: brand.riskMedium, light: "#FBBF24", dark: "#B45309" },
    error: { main: brand.riskHigh, light: "#F87171", dark: "#B91C1C" },
    info: { main: "#0EA5E9", light: "#38BDF8", dark: "#0369A1" },
    divider: "rgba(15, 23, 42, 0.08)",
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: "3rem", fontWeight: 800, letterSpacing: "-0.02em" },
    h2: { fontSize: "2.25rem", fontWeight: 800, letterSpacing: "-0.01em" },
    h3: { fontSize: "1.875rem", fontWeight: 700, letterSpacing: "-0.01em" },
    h4: { fontSize: "1.5rem", fontWeight: 700 },
    h5: { fontSize: "1.25rem", fontWeight: 700 },
    h6: { fontSize: "1.05rem", fontWeight: 700 },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    button: { fontWeight: 600, textTransform: "none" },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: "thin",
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 10,
          padding: "8px 18px",
          fontWeight: 600,
        },
        contained: {
          boxShadow: "none",
          "&:hover": {
            boxShadow: "0px 6px 16px rgba(37, 99, 235, 0.25)",
          },
        },
        sizeLarge: {
          padding: "12px 26px",
          fontSize: "1rem",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow:
            "0px 1px 2px rgba(15, 23, 42, 0.04), 0px 4px 16px rgba(15, 23, 42, 0.06)",
          border: "1px solid rgba(15, 23, 42, 0.04)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        rounded: { borderRadius: 14 },
        elevation1: {
          boxShadow:
            "0px 1px 2px rgba(15, 23, 42, 0.04), 0px 4px 16px rgba(15, 23, 42, 0.06)",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, borderRadius: 8 },
      },
    },
    MuiTextField: {
      defaultProps: { variant: "outlined" },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { borderRadius: 10 },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          color: "#334155",
          backgroundColor: "#F8FAFC",
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: { height: 3, borderRadius: 3 },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600 },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: { boxShadow: "0px 1px 2px rgba(15, 23, 42, 0.06)" },
      },
    },
  },
});

export default theme;
