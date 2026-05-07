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
      }}
    >
      <img
        src={item.image}
        alt={item.title}
        style={{
          width: "100%",
          height: "120px",
          objectFit: "cover",
          borderRadius: "8px",
        }}
      />
      <h4 style={{ margin: "8px 0" }}>{item.title}</h4>
      <p style={{ color: "#2d5a27", fontWeight: "bold" }}>{item.price} TL</p>
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
