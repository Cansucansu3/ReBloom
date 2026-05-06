import React, { useEffect, useState } from "react";
import { clearToken, getMe, getToken, login, register } from "../api/api";
import { getTreeStage } from "../utils/gamificationLogic";

const ProfileScreen = ({ totalWaterSaved, onAuthChange }) => {
  const currentStage = getTreeStage(totalWaterSaved);
  const [mode, setMode] = useState("login");
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    location: "",
  });

  useEffect(() => {
    if (!getToken()) return;

    getMe()
      .then(setUser)
      .catch((err) => {
        if (err.status === 401) {
          clearToken();
        }
      });
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      if (mode === "register") {
        await register({
          name: form.name,
          email: form.email,
          password: form.password,
          location: form.location || null,
        });
      }

      await login(form.email, form.password);
      const profile = await getMe();
      setUser(profile);
      onAuthChange?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    clearToken();
    setUser(null);
    onAuthChange?.();
  };

  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <div
        style={{
          background: "white",
          padding: "20px",
          borderRadius: "15px",
          boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
        }}
      >
        <h2>My Impact Profile</h2>

        {user ? (
          <div style={{ marginBottom: "16px" }}>
            <p style={{ margin: "4px 0", fontWeight: "bold" }}>{user.name}</p>
            <p style={{ margin: "4px 0", color: "#666" }}>{user.email}</p>
            <button onClick={handleLogout} style={styles.secondaryBtn}>
              Logout
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={styles.authForm}>
            <div style={styles.modeRow}>
              <button
                type="button"
                onClick={() => setMode("login")}
                style={mode === "login" ? styles.activeModeBtn : styles.modeBtn}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                style={mode === "register" ? styles.activeModeBtn : styles.modeBtn}
              >
                Register
              </button>
            </div>

            {mode === "register" && (
              <>
                <input
                  placeholder="Name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  style={styles.input}
                />
                <input
                  placeholder="Location"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  style={styles.input}
                />
              </>
            )}

            <input
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              style={styles.input}
            />
            <input
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              style={styles.input}
            />
            {error && <p style={{ color: "#b00020", margin: 0 }}>{error}</p>}
            <button type="submit" style={styles.primaryBtn}>
              {mode === "login" ? "Login" : "Create Account"}
            </button>
          </form>
        )}

        <div
          style={{
            margin: "20px auto",
            padding: "20px",
            background: "#e8f5e9",
            borderRadius: "50%",
            width: "140px",
            height: "140px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <span style={{ fontSize: "60px" }}>
            {currentStage === "Seed" && "Seed"}
            {currentStage === "Sapling" && "Sapling"}
            {currentStage === "Young Tree" && "Tree"}
            {currentStage === "Mature Oak" && "Oak"}
            {currentStage === "Ancient Oak" && "Ancient Oak"}
          </span>
          <p>
            <strong>{currentStage}</strong>
          </p>
        </div>

        <div
          style={{
            height: "20px",
            width: "100%",
            backgroundColor: "#eee",
            borderRadius: "10px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              backgroundColor: "#4A90E2",
              width: `${Math.min((totalWaterSaved / 500000) * 100, 100)}%`,
              transition: "width 0.5s",
            }}
          ></div>
        </div>

        <p style={{ fontWeight: "bold", marginTop: "10px" }}>
          {totalWaterSaved.toLocaleString()} / 500000 L saved
        </p>
      </div>
    </div>
  );
};

const styles = {
  authForm: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    margin: "0 auto 16px",
    maxWidth: "320px",
  },
  modeRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
  },
  modeBtn: {
    padding: "10px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    background: "white",
    color: "#2d5a27",
    cursor: "pointer",
  },
  activeModeBtn: {
    padding: "10px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    background: "#2d5a27",
    color: "white",
    cursor: "pointer",
  },
  input: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ddd",
  },
  primaryBtn: {
    background: "#2d5a27",
    color: "white",
    padding: "12px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  secondaryBtn: {
    background: "white",
    color: "#2d5a27",
    padding: "8px 12px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    cursor: "pointer",
  },
};

export default ProfileScreen;
