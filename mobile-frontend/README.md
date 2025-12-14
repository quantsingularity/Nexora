# Nexora Mobile Frontend

A React Native (Expo) mobile application for healthcare professionals to access patient risk predictions and clinical decision support on-the-go.

## Features

- **Patient List**: View and search through patient risk scores
- **Risk Predictions**: Detailed risk analysis with SHAP explanations
- **Real-time Updates**: Pull-to-refresh for latest patient data
- **Offline Support**: Fallback to cached data when code is unavailable
- **Secure Authentication**: Token-based authentication with AsyncStorage

## Tech Stack

- **Framework**: React Native with Expo SDK 52
- **Navigation**: React Navigation v7
- **State Management**: React Hooks
- **API Client**: Axios
- **Charts**: React Native Chart Kit
- **Testing**: Jest + React Native Testing Library + Detox

## Prerequisites

- Node.js 18+ and npm/yarn
- Expo CLI (`npm install -g expo-cli`)
- For iOS: Xcode and iOS Simulator (macOS only)
- For Android: Android Studio and Android Emulator
- code API running (see main project README)

## Installation

### 1. Install Dependencies

```bash
cd mobile-frontend
npm install
# or
yarn install
```

### 2. Configure Environment

Copy the example environment file and update with your code URL:

```bash
cp .env.example .env
```

Edit `.env` and set:

```env
API_BASE_URL=http://YOUR_code_HOST:8000

# For Android Emulator use: http://10.0.2.2:8000
# For iOS Simulator use: http://localhost:8000
# For physical device use: http://YOUR_MACHINE_IP:8000
```

### 3. Start Development Server

```bash
npm start
# or
yarn start
```

This will start the Expo development server. You can then:

- Press `i` to open iOS simulator
- Press `a` to open Android emulator
- Scan QR code with Expo Go app on your physical device

## Running on Devices/Emulators

### iOS Simulator (macOS only)

```bash
npm run ios
# or
yarn ios
```

### Android Emulator

```bash
npm run android
# or
yarn android
```

## Testing

### Unit Tests

Run all unit tests with Jest:

```bash
npm test
# or
yarn test
```

Run tests in watch mode:

```bash
npm run test:watch
# or
yarn test:watch
```

Generate coverage report:

```bash
npm run test:coverage
# or
yarn test:coverage
```

### End-to-End Tests

E2E tests use Detox. First, build the app for testing:

**iOS:**

```bash
npm run e2e:build:ios
npm run e2e:test:ios
```

**Android:**

```bash
npm run e2e:build:android
npm run e2e:test:android
```

## Project Structure

```
mobile-frontend/
├── App.js                 # Root component
├── app.json               # Expo configuration
├── babel.config.js        # Babel configuration with env support
├── .env.example           # Environment variables template
├── assets/                # Static assets (icons, splash screens)
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Card.js
│   │   ├── CustomButton.js
│   │   ├── CustomInput.js
│   │   ├── PatientCard.js
│   │   ├── ScreenWrapper.js
│   │   └── __tests__/     # Component tests
│   ├── navigation/        # Navigation configuration
│   │   └── AppNavigator.js
│   ├── screens/           # Screen components
│   │   ├── HomeScreen.js
│   │   ├── LoginScreen.js
│   │   ├── PatientDetailScreen.js
│   │   └── __tests__/     # Screen tests
│   ├── services/          # API and external services
│   │   ├── api.js
│   │   └── __tests__/     # Service tests
│   ├── theme/             # Design system (colors, typography, spacing)
│   │   └── theme.js
│   └── __mocks__/         # Mock data for testing
│       └── mockData.js
└── e2e/                   # End-to-end tests (Detox)
    ├── firstTest.e2e.js
    └── patient-workflow.e2e.js
```

## code Integration

The mobile app integrates with the Nexora code API. Make sure the code is running before using the app.

### Available Endpoints

The app uses these code endpoints:

- `GET /health` - Health check
- `GET /models` - List available prediction models
- `POST /predict` - Submit prediction request
- `POST /fhir/patient/{id}/predict` - FHIR patient prediction

### Fallback Mock Data

If the code is unavailable, the app falls back to mock data for development and testing. This allows developers to work on the UI without requiring a running code.

## Authentication

**Demo Credentials:**

- Username: `clinician`
- Password: `password123`

In production, replace the mock authentication in `src/services/api.js` with your actual authentication implementation.

## Configuration

### App Configuration

Edit `app.json` to customize:

- App name and description
- Bundle identifiers (iOS/Android)
- App icons and splash screens
- Build settings

### Theme Customization

Edit `src/theme/theme.js` to customize:

- Colors (primary, secondary, error, success, etc.)
- Typography (font sizes, weights)
- Spacing (padding, margins)

## Troubleshooting

### Common Issues

**1. Metro bundler cache issues:**

```bash
expo start --clear
```

**2. iOS build fails:**

```bash
cd ios && pod install && cd ..
```

**3. Android build fails:**

- Ensure Android SDK is properly installed
- Check ANDROID_HOME environment variable
- Clean build: `cd android && ./gradlew clean && cd ..`

**4. Cannot connect to code:**

- Verify code is running
- Check API_BASE_URL in .env
- For Android emulator, use `10.0.2.2` instead of `localhost`
- For physical device, ensure both device and computer are on same network

### Network Debugging

To view API requests/responses, enable network debugging:

1. Shake device (or Cmd+D on iOS, Cmd+M on Android)
2. Select "Debug Remote JS"
3. Open Chrome DevTools Console
4. View network requests in console.log

## Building for Production

### iOS

```bash
expo build:ios
```

### Android

```bash
expo build:android
```

Follow Expo's build documentation for detailed instructions on app store submissions.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Add/update tests
4. Ensure all tests pass: `npm test`
5. Submit a pull request

## License

MIT License - see LICENSE file for details
