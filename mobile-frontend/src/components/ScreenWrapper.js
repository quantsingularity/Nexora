import React from 'react';
import { View, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import { Colors, GlobalStyles } from '../theme/theme';

const ScreenWrapper = ({ children, style, useSafeArea = true }) => {
  const WrapperComponent = useSafeArea ? SafeAreaView : View;

  return (
    <WrapperComponent style={[styles.safeArea, style]}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />
      <View style={styles.container}>
        {children}
      </View>
    </WrapperComponent>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    ...GlobalStyles.container,
  },
});

export default ScreenWrapper;

