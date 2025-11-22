# Mobile Frontend Directory

## Overview

The mobile-frontend directory contains the React Native application that serves as the mobile client interface for the Nexora system. This cross-platform mobile application provides healthcare professionals with on-the-go access to patient data, clinical predictions, and decision support tools, optimized for smartphone and tablet devices.

## Directory Structure

```
mobile-frontend/
├── .detoxrc.js
├── .expo/
│   ├── README.md
│   └── devices.json
├── App.js
├── app.json
├── assets/
│   ├── adaptive-icon.png
│   ├── favicon.png
│   ├── icon.png
│   └── splash-icon.png
├── e2e/
│   ├── firstTest.e2e.js
│   └── patient-workflow.e2e.js
├── index.js
├── jest.config.js
├── package-lock.json
├── package.json
├── src/
│   ├── __tests__/
│   │   └── App.test.js
│   ├── components/
│   │   ├── Card.js
│   │   ├── CustomButton.js
│   │   ├── CustomInput.js
│   │   ├── ScreenWrapper.js
│   │   └── __tests__/
│   │       └── PatientCard.test.js
│   ├── navigation/
│   │   └── AppNavigator.js
│   ├── screens/
│   │   ├── HomeScreen.js
│   │   ├── LoginScreen.js
│   │   └── PatientDetailScreen.js
│   ├── services/
│   │   └── api.js
│   └── theme/
│       └── theme.js
└── yarn.lock
```

## Contents Description

### Root Files

- **App.js**: The main application component that serves as the entry point for the React Native app.
- **app.json**: Configuration file for Expo, containing app metadata like name, version, and platform-specific settings.
- **index.js**: JavaScript entry point that registers the main App component.
- **.detoxrc.js**: Configuration file for Detox, an end-to-end testing framework for mobile apps.
- **jest.config.js**: Configuration file for Jest testing framework.
- **package.json**: Node.js package configuration file defining dependencies, scripts, and metadata.
- **yarn.lock** and **package-lock.json**: Lock files ensuring consistent dependency installations.

### Subdirectories

#### .expo/

Contains Expo-specific configuration files:

- **README.md**: Documentation for Expo configuration.
- **devices.json**: Configuration for Expo development devices.

#### assets/

Contains static assets used in the application:

- **icon.png**: Main application icon.
- **adaptive-icon.png**: Adaptive icon for Android devices.
- **favicon.png**: Favicon for web versions of the app.
- **splash-icon.png**: Image displayed during app loading.

#### e2e/

Contains end-to-end tests using Detox:

- **firstTest.e2e.js**: Initial test suite for basic app functionality.
- **patient-workflow.e2e.js**: Tests for patient-related workflows.

#### src/

Contains the main source code for the application:

- \***\*tests**/\*\*: Unit tests for the application components.
  - **App.test.js**: Tests for the main App component.

- **components/**: Reusable UI components.
  - **Card.js**: Generic card component for displaying content.
  - **CustomButton.js**: Styled button component.
  - **CustomInput.js**: Styled input component.
  - **ScreenWrapper.js**: Wrapper component for consistent screen layouts.
  - \***\*tests**/PatientCard.test.js\*\*: Tests for the PatientCard component.

- **navigation/**: Navigation configuration.
  - **AppNavigator.js**: Main navigation structure using React Navigation.

- **screens/**: Screen components representing full pages in the app.
  - **HomeScreen.js**: Main dashboard screen.
  - **LoginScreen.js**: Authentication screen.
  - **PatientDetailScreen.js**: Detailed patient information screen.

- **services/**: Service modules for external interactions.
  - **api.js**: API client for communicating with the backend services.

- **theme/**: Styling and theming.
  - **theme.js**: Theme configuration including colors, typography, and spacing.

## Setup and Installation

To set up the mobile frontend for development:

1. **Install dependencies**:

   ```bash
   cd mobile-frontend
   npm install
   # or
   yarn install
   ```

2. **Start the development server**:

   ```bash
   npm start
   # or
   yarn start
   ```

3. **Run on a device or emulator**:

   ```bash
   # For iOS
   npm run ios
   # or
   yarn ios

   # For Android
   npm run android
   # or
   yarn android
   ```

## Testing

The mobile frontend includes several types of tests:

1. **Unit Tests** (using Jest):

   ```bash
   npm test
   # or
   yarn test
   ```

2. **End-to-End Tests** (using Detox):

   ```bash
   # Build the app for testing
   detox build --configuration ios.sim

   # Run the tests
   detox test --configuration ios.sim
   ```
