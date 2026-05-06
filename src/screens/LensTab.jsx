import React, { useState } from "react";
import { calculateSavings } from "../utils/gamificationLogic";

const LensTab = ({ onListingSaved }) => {
  const [preview, setPreview] = useState(null);
  const [step, setStep] = useState(1);
  const [metadata, setMetadata] = useState({
    title: "",
    brand: "",
    size: "M",
    color: "",
    gender: "Unisex",
    fabric: "Denim",
    weight: 0.5,
    price: "",
  });

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
      setStep(2);
    }
  };

  const currentSavings = calculateSavings(metadata.fabric, metadata.weight);

  if (step === 2)
    return (
      <div style={styles.formScroll}>
        <img src={preview} style={styles.formImg} alt="Preview" />
        <h3 style={{ textAlign: "center" }}>Item Details</h3>

        <label style={styles.label}>Item Title</label>
        <input
          type="text"
          placeholder="e.g. Black Velvet Jacket"
          onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
          style={styles.input}
        />

        <label style={styles.label}>Price (TL)</label>
        <input
          type="number"
          placeholder="2000"
          onChange={(e) => setMetadata({ ...metadata, price: e.target.value })}
          style={styles.input}
        />

        <div style={styles.row}>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Brand</label>
            <input
              type="text"
              placeholder="e.g. BDG"
              onChange={(e) =>
                setMetadata({ ...metadata, brand: e.target.value })
              }
              style={styles.input}.
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Size</label>
            <input
              type="text"
              placeholder="e.g. M / 38"
              onChange={(e) =>
                setMetadata({ ...metadata, size: e.target.value })
              }
              style={styles.input}
            />
          </div>
        </div>
        <div style={styles.row}>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Color</label>
            <input
              type="text"
              placeholder="e.g. Charcoal"
              onChange={(e) =>
                setMetadata({ ...metadata, color: e.target.value })
              }
              style={styles.input}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Gender</label>
            <select
              onChange={(e) =>
                setMetadata({ ...metadata, gender: e.target.value })
              }
              style={styles.input}
            >
              <option value="Unisex">Unisex</option>
              <option value="Women">Women</option>
              <option value="Men">Men</option>
            </select>
          </div>
        </div>

        <label style={styles.label}>Fabric (for Water Impact)</label>
        <select
          onChange={(e) => setMetadata({ ...metadata, fabric: e.target.value })}
          style={styles.input}
        >
          <option value="Denim">Denim</option>
          <option value="Cotton">Cotton</option>
          <option value="Polyester">Polyester</option>
        </select>

        <button
          onClick={() =>
            onListingSaved({ ...metadata, preview }, currentSavings)
          }
          style={styles.primaryBtn}
        >
          Confirm & List
        </button>
      </div>
    );

  return (
    <div style={{ textAlign: "center", paddingTop: "100px" }}>
      <label style={styles.uploadBtn}>
        📸 Upload Photo
        <input
          type="file"
          onChange={handleUpload}
          style={{ display: "none" }}
        />
      </label>
    </div>
  );
};

const styles = {
  formScroll: {
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    maxWidth: "400px",
    margin: "auto",
  },
  formImg: {
    width: "100px",
    height: "100px",
    objectFit: "cover",
    borderRadius: "10px",
    alignSelf: "center",
  },
  row: { display: "flex", gap: "10px" },
  label: { fontSize: "12px", fontWeight: "bold", color: "#666" },
  input: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    width: "100%",
    boxSizing: "border-box",
  },
  primaryBtn: {
    background: "#2d5a27",
    color: "white",
    padding: "15px",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  uploadBtn: {
    background: "#2d5a27",
    color: "white",
    padding: "20px",
    borderRadius: "10px",
    cursor: "pointer",
  },
};

export default LensTab;
