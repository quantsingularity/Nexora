# Nexora Web Frontend

## Quick Start

```bash
# Install dependencies
npm ci

# Start development server (uses mock data by default)
npm start

# Run tests
npm test

# Run E2E tests (requires dev server running)
npm run test:e2e

# Build for production
npm run build
```

## Project Structure

```
web-frontend/
├── src/
│   ├── pages/                    # Page components
│   │   ├── Dashboard.js          # Main dashboard with charts
│   │   ├── PatientList.js        # Patient list with search/filter
│   │   ├── PatientDetail.js      # Patient details with tabs
│   │   ├── PredictionModels.js   # Model management
│   │   ├── Settings.js           # App settings
│   │   └── __tests__/            # Page tests (NEW)
│   ├── components/               # Reusable components
│   │   ├── Layout.js             # Main layout with navigation (UPDATED)
│   │   ├── ErrorBoundary.js      # Error handling (NEW)
│   │   └── __tests__/            # Component tests (NEW)
│   ├── services/
│   │   └── api.js                # API client (UPDATED)
│   ├── assets/
│   │   └── styles/
│   │       └── theme.js          # Material-UI theme
│   ├── App.js                    # Root component
│   ├── index.js                  # Entry point (UPDATED)
│   ├── index.html                # HTML template
│   └── setupTests.js             # Jest setup (NEW)
├── cypress/
│   └── e2e/
│       └── patient-workflow.cy.js # E2E tests (UPDATED)
├── __mocks__/                    # Test mocks (NEW)
├── .env                          # Dev environment (NEW)
├── .env.example                  # Env template (NEW)
├── .babelrc                      # Babel config (NEW)
├── cypress.config.js             # Cypress config (NEW)
├── jest.config.js                # Jest config (UPDATED)
├── package.json                  # Dependencies (UPDATED)
├── CHANGES.md                    # Detailed changes (NEW)
└── README_UPDATED.md             # This file (NEW)
```

## Features

### 1. Clinical Dashboard

- Real-time statistics (Active Patients, High Risk, Avg Length of Stay, Active Models)
- Admissions & Readmissions trend chart
- Patient Risk Distribution (doughnut chart)
- Model Performance metrics (bar chart)
- Generate Report button

### 2. Patient Management

- Searchable patient list
- Pagination (5, 10, 25 rows per page)
- Risk score badges with color coding
- Patient detail view with tabs:
  - Clinical Data (lab results, diagnoses)
  - Risk Analysis (risk factors, interventions)
  - Medications (current prescriptions)
  - Timeline (clinical history)

### 3. Prediction Models

- List of available models with version info
- Model status indicators (Active/Inactive)
- Tabs for:
  - Performance metrics (AUC, Accuracy, Precision, Recall, F1)
  - Training history (loss curves)
  - Configuration (model settings, feature toggles)
- Deploy and Export buttons

### 4. Settings

- User Profile management
- Security settings (2FA, session timeouts)
- Notification preferences
- Data source management
- System information and health check

### 5. Navigation & UX

- Responsive sidebar navigation
- Active page highlighting
- Mobile-friendly drawer
- Profile menu with user options
- System status indicator
- Notification badge

## Environment Configuration

### Development (.env)

```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_USE_MOCK_DATA=true
REACT_APP_ENABLE_DEBUG_MODE=false
```

### Production

```env
REACT_APP_API_BASE_URL=https://api.nexora.com
REACT_APP_USE_MOCK_DATA=false
REACT_APP_ENABLE_DEBUG_MODE=false
```

### Available Variables

- `REACT_APP_API_BASE_URL` - Backend API URL
- `REACT_APP_API_TIMEOUT` - Request timeout (ms)
- `REACT_APP_USE_MOCK_DATA` - Use mock data (true/false)
- `REACT_APP_ENABLE_DEBUG_MODE` - Enable debug features
- `REACT_APP_DEFAULT_RECORDS_PER_PAGE` - Pagination default
- `REACT_APP_MAX_FILE_UPLOAD_SIZE` - Upload size limit

## Backend Integration

### API Endpoints Expected

The frontend expects these endpoints from the backend:

```
GET  /health                      # Health check
GET  /models                      # List available models
GET  /patients                    # List patients
GET  /patients/:id                # Get patient details
GET  /dashboard                   # Get dashboard data
POST /predict                     # Make prediction
POST /fhir/patient/:id/predict    # FHIR-based prediction
```

### Response Formats

#### Dashboard Data

```json
{
  "stats": {
    "activePatients": 1284,
    "highRiskPatients": 256,
    "avgLengthOfStay": 4.2,
    "activeModels": 5
  },
  "patientRiskDistribution": {
    "highRisk": 25,
    "mediumRisk": 45,
    "lowRisk": 30
  },
  "admissionsData": {
    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "admissions": [65, 59, 80, 81, 56, 55],
    "readmissions": [28, 48, 40, 19, 36, 27]
  },
  "modelPerformance": {
    "labels": ["Readmission", "Mortality", "LOS", "Complications"],
    "scores": [0.82, 0.78, 0.75, 0.81]
  }
}
```

#### Patient List

```json
{
  "patients": [
    {
      "id": "P00001",
      "name": "John Doe",
      "age": 45,
      "gender": "Male",
      "diagnosis": "Hypertension",
      "lastVisit": "2025-04-01",
      "riskScore": 0.35
    }
  ]
}
```

### Mock Data Mode

When `REACT_APP_USE_MOCK_DATA=true`, the app uses realistic mock data for all API calls. This enables:

- Development without backend
- Demos and presentations
- Testing UI independently
- Frontend-only deployments

The API service automatically falls back to mock data if real API calls fail, ensuring the app always works.

## Testing

### Unit Tests (Jest + React Testing Library)

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage
```

**Test Coverage:**

- Dashboard: ~80%
- PatientList: ~85%
- PatientDetail: ~75%
- Settings: ~80%
- PredictionModels: ~75%
- Layout: ~70%
- **Overall: ~77%**

### E2E Tests (Cypress)

```bash
# Headless (for CI)
npm run test:e2e

# Interactive (for development)
npm run test:e2e:open
```

## Building for Production

```bash
# Standard build
npm run build

# Build with specific environment
NODE_ENV=production REACT_APP_API_BASE_URL=https://api.nexora.com npm run build
```

This creates a `dist/` directory with:

- Minified JavaScript bundles
- Optimized CSS
- Compressed assets
- Source maps (for debugging)

### Deployment Options

#### Static Hosting

```bash
# Serve locally
npx serve dist

# Deploy to Netlify
netlify deploy --prod --dir=dist

# Deploy to Vercel
vercel --prod

# Deploy to S3
aws s3 sync dist/ s3://your-bucket/ --delete
```

## License

MIT License - See LICENSE file for details
