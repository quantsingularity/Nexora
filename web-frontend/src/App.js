import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { ProtectedRoute, PublicOnlyRoute } from "./components/ProtectedRoute";
import Alerts from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import Homepage from "./pages/Homepage";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import PatientDetail from "./pages/PatientDetail";
import PatientList from "./pages/PatientList";
import PredictionModels from "./pages/PredictionModels";
import Settings from "./pages/Settings";
import SignUp from "./pages/SignUp";

function App() {
  return (
    <Routes>
      {/* Public marketing page: always the first thing a visitor sees */}
      <Route path="/" element={<Homepage />} />

      {/* Auth pages: redirect to /dashboard if already signed in */}
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicOnlyRoute>
            <SignUp />
          </PublicOnlyRoute>
        }
      />

      {/* App pages: require sign-in, rendered inside the sidebar Layout */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
        <Route path="/models" element={<PredictionModels />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      {/* 404 catch-all */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
