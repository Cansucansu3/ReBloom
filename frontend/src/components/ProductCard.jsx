import React from "react";
import { calculateSavings } from "../utils/gamificationLogic";

const ProductCard = ({ item, onClick }) => {
  const savings = Math.round(
    Number(item.waterSaved ?? item.water_saved_liters) ||
      calculateSavings(item.fabric, item.weight)
  );

  return (
    <div
      onClick={onClick}
      style={{
        border: "1px solid #ddd",
        borderRadius: "12px",
        width: "180px",
        margin: "10px",
        padding: "10px",
        backgroundColor: "white",
        cursor: "pointer",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "140px",
          borderRadius: "8px",
          background: "#f8faf8",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        <img
          src={item.image}
          alt={item.title}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
        />
      </div>
      <h4
        style={{
          margin: "8px 0",
          minHeight: "44px",
          color: "#625b70",
          lineHeight: 1.25,
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {item.title}
      </h4>
      <p style={{ color: "#2d5a27", fontWeight: "bold", marginBottom: "8px" }}>
        {item.price} TL
      </p>
      <div
        style={{
          backgroundColor: "#e3f2fd",
          padding: "4px",
          borderRadius: "4px",
          fontSize: "11px",
          color: "#1976d2",
        }}
      >
        Saves {savings.toLocaleString()}L
      </div>
    </div>
  );
};

export default ProductCard;
