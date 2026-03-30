import { Box } from "@mui/material";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import PatientDetail from "./pages/PatientDetail";
import PatientList from "./pages/PatientList";
import PredictionModels from "./pages/PredictionModels";
import Settings from "./pages/Settings";

function App() {
  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="patients" element={<PatientList />} />
          <Route path="patients/:id" element={<PatientDetail />} />
          <Route path="models" element={<PredictionModels />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Box>
  );
}

export default App;
