export const Colors = {
  primary: '#007AFF', // Apple Blue
  secondary: '#5856D6', // Apple Purple
  accent: '#FF9500', // Apple Orange
  background: '#F2F2F7', // System Gray 6 Light
  surface: '#FFFFFF', // White
  text: '#000000', // Black
  textSecondary: '#8E8E93', // System Gray Light
  error: '#FF3B30', // Apple Red
  success: '#34C759', // Apple Green
  warning: '#FFCC00', // Apple Yellow
  border: '#C6C6C8', // System Gray 4 Light
  disabled: '#D1D1D6', // System Gray 5 Light
};

export const Typography = {
  h1: { fontSize: 34, fontWeight: 'bold' },
  h2: { fontSize: 28, fontWeight: 'bold' },
  h3: { fontSize: 22, fontWeight: 'bold' },
  h4: { fontSize: 20, fontWeight: 'bold' },
  body1: { fontSize: 17, fontWeight: 'normal' },
  body2: { fontSize: 15, fontWeight: 'normal' },
  caption: { fontSize: 13, fontWeight: 'normal' },
  button: { fontSize: 17, fontWeight: '600' },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const GlobalStyles = {
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    padding: Spacing.md,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  // Add other global styles as needed
};

