import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken, clearToken, hasToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refreshUser() {
    if (!hasToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get("/auth/me");
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshUser();
  }, []);

  async function login(email, password) {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);

    const data = await api.postForm("/auth/login", body);
    setToken(data.access_token);
    await refreshUser();
  }

  async function register(fullName, email, password, role, providerId) {
    await api.post("/auth/register", {
      full_name: fullName,
      email,
      password,
      role,
      provider_id: providerId || null,
    });
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
