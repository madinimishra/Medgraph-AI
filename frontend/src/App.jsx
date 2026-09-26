import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import GraphStats from "./pages/GraphStats";
import Patients from "./pages/Patients";
import NetworkDashboard from "./pages/NetworkDashboard";
import AuditLog from "./pages/AuditLog";
import Admin from "./pages/Admin";
import About from "./pages/About";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<About />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/chat" element={<Chat />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/graph" element={<GraphStats />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/network" element={<NetworkDashboard />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/admin" element={<Admin />} />
        </Route>

        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </AuthProvider>
  );
}
