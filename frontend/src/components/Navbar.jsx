import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Logo from "./Logo";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="navbar">
      <Link to="/about" className="navbar-brand-block">
        <Logo size={30} />
        <div>
          <div className="navbar-brand">MedGraph AI</div>
          <div className="navbar-tagline">See the network behind the data</div>
        </div>
      </Link>
      <div className="navbar-links">
        <NavLink to="/chat" className={({ isActive }) => (isActive ? "active" : "")}>
          Chat
        </NavLink>
        <NavLink to="/documents" className={({ isActive }) => (isActive ? "active" : "")}>
          Documents
        </NavLink>
        <NavLink to="/patients" className={({ isActive }) => (isActive ? "active" : "")}>
          Patients
        </NavLink>
        <NavLink to="/network" className={({ isActive }) => (isActive ? "active" : "")}>
          Network
        </NavLink>
        <NavLink to="/graph" className={({ isActive }) => (isActive ? "active" : "")}>
          Graph
        </NavLink>
        {user?.role === "admin" && (
          <>
            <NavLink to="/audit" className={({ isActive }) => (isActive ? "active" : "")}>
              Audit
            </NavLink>
            <NavLink to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>
              Admin
            </NavLink>
          </>
        )}
      </div>
      <div className="navbar-user">
        {user && (
          <>
            <span className="navbar-username">
              {user.full_name} · {user.role}
            </span>
            <button className="navbar-logout" onClick={handleLogout}>
              Log out
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
