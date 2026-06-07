import React, { useEffect, useState } from "react";
import {
  clearToken,
  getMe,
  getMyImpact,
  getToken,
  login,
  register,
} from "../api/api";
import VirtualGardenCard from "../components/VirtualGardenCard";

const ProfileScreen = ({ totalWaterSaved, onAuthChange }) => {
  const [impactWaterSaved, setImpactWaterSaved] = useState(totalWaterSaved || 0);
  const [impactStats, setImpactStats] = useState({
    total_items_reused: 0,
    virtual_trees: 0,
    real_trees_earned: 0,
    impact_points: 0,
    legacy_certificate: null,
  });
  const [mode, setMode] = useState("login");
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);
  const [impactError, setImpactError] = useState("");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    location: "",
  });

  const refreshImpact = async () => {
    try {
      const impact = await getMyImpact();
      setImpactWaterSaved(Math.round(impact.total_water_saved_liters || 0));
      setImpactStats({
        total_items_reused: impact.total_items_reused || 0,
        virtual_trees: impact.virtual_trees || 0,
        real_trees_earned: impact.real_trees_earned || 0,
        impact_points: impact.impact_points || 0,
        legacy_certificate: impact.legacy_certificate || null,
      });
      setImpactError("");
    } catch (err) {
      setImpactWaterSaved(0);
      setImpactStats({
        total_items_reused: 0,
        virtual_trees: 0,
        real_trees_earned: 0,
        impact_points: 0,
        legacy_certificate: null,
      });
      setImpactError("Impact data could not be loaded.");
      if (err.status === 401) {
        throw err;
      }
    }
  };

  const loadProfile = async () => {
    if (!getToken()) return;

    setProfileLoading(true);
    setError("");

    try {
      const profile = await getMe();
      setUser(profile);

      try {
        await refreshImpact();
      } catch (impactErr) {
        if (impactErr.status === 401) {
          throw impactErr;
        }
      }
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        setUser(null);
        setImpactWaterSaved(0);
      } else {
        setError(err.message || "Profile could not be loaded.");
      }
    } finally {
      setProfileLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
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
      await loadProfile();
      onAuthChange?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    clearToken();
    setUser(null);
    setImpactWaterSaved(0);
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

        {profileLoading && !user ? (
          <p style={{ color: "#666" }}>Loading profile...</p>
        ) : user ? (
          <div style={{ marginBottom: "16px" }}>
            <p style={{ margin: "4px 0", fontWeight: "bold" }}>{user.name}</p>
            <p style={{ margin: "4px 0", color: "#2d5a27", fontWeight: "bold" }}>
              {makeUsername(user.name)}
            </p>
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

        <div style={{ marginTop: "18px" }}>
          <VirtualGardenCard impact={impactStats} totalWaterSaved={impactWaterSaved} />
        </div>

        {impactError && (
          <p style={{ color: "#8a6d3b", fontSize: "13px", margin: "6px 0 0" }}>
            {impactError}
          </p>
        )}
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
  gardenCard: {
    marginTop: "18px",
    background: "#f8faf8",
    border: "1px solid #dceadc",
    borderRadius: "18px",
    padding: "18px",
  },
  treeImageWrap: {
    width: "190px",
    height: "190px",
    margin: "0 auto 8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  treeImage: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
  },
  stageEyebrow: {
    margin: "4px 0 2px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  stageTitle: {
    margin: "0",
    color: "#1f3f1c",
    fontSize: "26px",
  },
  stageCopy: {
    margin: "6px 0 14px",
    color: "#5f6f5e",
    fontSize: "14px",
  },
  progressTrack: {
    height: "18px",
    width: "100%",
    backgroundColor: "#e5ece4",
    borderRadius: "999px",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#4f8f45",
    borderRadius: "999px",
    transition: "width 0.5s",
  },
  progressLabel: {
    margin: "10px 0 2px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  progressText: {
    fontWeight: "bold",
    color: "#4f4a5f",
    margin: "0 0 4px",
  },
  totalWaterText: {
    color: "#2d5a27",
    fontWeight: "bold",
    margin: "0 0 14px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
    gap: "8px",
  },
  statBox: {
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "12px",
    padding: "10px 6px",
    display: "grid",
    gap: "3px",
    color: "#2d5a27",
  },
  gardenStrip: {
    marginTop: "14px",
    display: "grid",
    gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
    gap: "8px",
  },
  gardenLevelText: {
    gridColumn: "1 / -1",
    margin: "0 0 4px",
    color: "#2d5a27",
    fontSize: "13px",
    fontWeight: "bold",
  },
  gardenPlot: {
    minHeight: "58px",
    borderRadius: "14px",
    background: "#edf4ec",
    border: "1px dashed #bdd7ba",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  gardenPlotFilled: {
    minHeight: "58px",
    borderRadius: "14px",
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  gardenTree: {
    width: "48px",
    height: "48px",
    objectFit: "contain",
  },
  emptyPlotDot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    background: "#bdd7ba",
  },
};

export default ProfileScreen;

function makeUsername(name) {
  const slug = String(name || "rebloom-user")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return `@${slug || "rebloom-user"}`;
}
