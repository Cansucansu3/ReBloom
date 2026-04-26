import React from "react";
import { getTreeStage } from "../utils/gamificationLogic";

// totalWaterSaved comes from App.jsx
const ProfileScreen = ({ totalWaterSaved }) => {
  const currentStage = getTreeStage(totalWaterSaved);

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

        <div
          style={{
            margin: "20px 0",
            padding: "20px",
            background: "#e8f5e9",
            borderRadius: "50%",
          }}
        >
          <span style={{ fontSize: "70px" }}>
            {currentStage === "Seed" && "🌱"}
            {currentStage === "Sapling" && "🌿"}
            {currentStage === "Young Tree" && "🌳"}
            {currentStage === "Mature Oak" && "🌲"}
            {currentStage === "Ancient Oak" && "✨🌳✨"}
          </span>
          <p>
            <strong>Stage: {currentStage}</strong>
          </p>
        </div>

        {/* Dynamic Progress Bar [cite: 521-523] */}
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
              width: `${Math.min((totalWaterSaved / 20000) * 100, 100)}%`,
              transition: "width 0.5s",
            }}
          ></div>
        </div>

        <p style={{ fontWeight: "bold", marginTop: "10px" }}>
          {totalWaterSaved.toLocaleString()} / 20,000 L saved
        </p>
      </div>
    </div>
  );
};

export default ProfileScreen;
