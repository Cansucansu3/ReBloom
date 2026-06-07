import React, { useEffect, useState } from "react";
import {
  clearToken,
  getLeaderboard,
  getMyImpact,
  getPublicUserProfile,
} from "../api/api";
import VirtualGardenCard from "../components/VirtualGardenCard";

const GardenScreen = ({ onAuthRequired, onSellerProfileSelect }) => {
  const [impact, setImpact] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadGarden() {
      setStatus("loading");
      setMessage("");

      try {
        const [impactData, leaderboardData] = await Promise.all([
          getMyImpact(),
          getLeaderboard(10),
        ]);

        if (!mounted) return;
        setImpact(impactData);
        setLeaderboard(leaderboardData || []);
        setStatus("ready");
      } catch (err) {
        if (err.status === 401) {
          clearToken();
          onAuthRequired?.();
          return;
        }

        if (!mounted) return;
        setMessage(err.message || "Garden could not be loaded.");
        setStatus("error");
      }
    }

    loadGarden();

    return () => {
      mounted = false;
    };
  }, [onAuthRequired]);

  const waterSaved = Number(impact?.total_water_saved_liters || 0);

  const handleLeaderboardClick = async (entry) => {
    setMessage("");

    try {
      const profile = await getPublicUserProfile(entry.user_id);
      onSellerProfileSelect?.(profile);
    } catch (err) {
      setMessage(err.message || "Profile could not be opened.");
    }
  };

  if (status === "loading") {
    return <p style={styles.statusText}>Loading garden...</p>;
  }

  if (status === "error") {
    return <p style={{ ...styles.statusText, color: "#b00020" }}>{message}</p>;
  }

  return (
    <div style={styles.page}>
      <VirtualGardenCard impact={impact} totalWaterSaved={waterSaved} />

      <section style={styles.leaderboard}>
        <h3 style={styles.sectionTitle}>Leaderboard</h3>
        {leaderboard.map((entry) => (
          <button
            key={entry.user_id}
            type="button"
            onClick={() => handleLeaderboardClick(entry)}
            style={styles.leaderboardRow}
          >
            <span style={styles.rank}>#{entry.rank}</span>
            <span style={styles.username}>{entry.username}</span>
            <span style={styles.leaderboardMeta}>
              {Math.round(Number(entry.water_saved_liters || 0)).toLocaleString()} L
            </span>
          </button>
        ))}
      </section>

      {message && <p style={styles.message}>{message}</p>}
    </div>
  );
};

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f8faf8",
    padding: "18px 16px 100px",
  },
  statusText: {
    textAlign: "center",
    padding: "40px 16px",
    color: "#555",
  },
  hero: {
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "18px",
    padding: "18px",
    textAlign: "center",
  },
  treeWrap: {
    width: "210px",
    height: "210px",
    margin: "0 auto",
  },
  mainTree: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
  },
  eyebrow: {
    margin: "0 0 4px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  title: {
    margin: 0,
    color: "#1f3f1c",
    fontSize: "30px",
  },
  copy: {
    margin: "8px 0 16px",
    color: "#5f6f5e",
  },
  progressTrack: {
    height: "18px",
    background: "#e5ece4",
    borderRadius: "999px",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    background: "#4f8f45",
    borderRadius: "999px",
  },
  progressLabel: {
    margin: "10px 0 2px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  progressText: {
    margin: "0 0 4px",
    color: "#4f4a5f",
    fontWeight: "bold",
  },
  totalWaterText: {
    margin: 0,
    color: "#2d5a27",
    fontWeight: "bold",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
    gap: "10px",
    marginTop: "14px",
  },
  stat: {
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "14px",
    padding: "12px 6px",
    display: "grid",
    gap: "4px",
    textAlign: "center",
    color: "#2d5a27",
  },
  gardenGrid: {
    marginTop: "14px",
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "10px",
  },
  gardenLevelHeader: {
    gridColumn: "1 / -1",
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "14px",
    padding: "12px",
    display: "flex",
    justifyContent: "space-between",
    gap: "10px",
    color: "#2d5a27",
    flexWrap: "wrap",
  },
  plot: {
    minHeight: "86px",
    borderRadius: "16px",
    background: "#edf4ec",
    border: "1px dashed #bdd7ba",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  plotFilled: {
    minHeight: "86px",
    borderRadius: "16px",
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  plotTree: {
    width: "70px",
    height: "70px",
    objectFit: "contain",
  },
  emptyDot: {
    width: "13px",
    height: "13px",
    borderRadius: "50%",
    background: "#bdd7ba",
  },
  leaderboard: {
    marginTop: "18px",
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "18px",
    padding: "14px",
  },
  sectionTitle: {
    margin: "0 0 10px",
    color: "#1f3f1c",
  },
  leaderboardRow: {
    width: "100%",
    display: "grid",
    gridTemplateColumns: "48px 1fr auto",
    gap: "10px",
    alignItems: "center",
    border: "none",
    borderTop: "1px solid #eef2ed",
    background: "transparent",
    padding: "12px 0",
    cursor: "pointer",
    textAlign: "left",
  },
  rank: {
    color: "#2d5a27",
    fontWeight: "bold",
  },
  username: {
    color: "#4f4a5f",
    fontWeight: "bold",
  },
  leaderboardMeta: {
    color: "#2d5a27",
    fontWeight: "bold",
    whiteSpace: "nowrap",
  },
  message: {
    color: "#8a2f2f",
    textAlign: "center",
  },
};

export default GardenScreen;
