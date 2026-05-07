import React, { useState } from "react";
import { createProduct, getToken } from "../api/api";

const LensTab = ({ onListingSaved, onAuthRequired }) => {
  const [preview, setPreview] = useState(null);
  const [step, setStep] = useState(1);
  const [isSaving, setIsSaving] = useState(false);
  const [metadata, setMetadata] = useState({
    title: "",
    category: "tops",
    brand: "",
    size: "M",
    color: "",
    gender: "Unisex",
    fabric: "100% Denim",
    weight: 0.5,
    price: "",
  });

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setPreview(reader.result);
      setStep(2);
    };
    reader.readAsDataURL(file);
  };

  const handleSaveListing = async () => {
    if (!getToken()) {
      alert("Ilan kaydetmek icin once Profile sekmesinden giris yapmalisin.");
      onAuthRequired?.();
      return;
    }

    setIsSaving(true);

    try {
      const savedProduct = await createProduct({
        title: metadata.title,
        description: metadata.title,
        category: metadata.category,
        subcategory: metadata.gender,
        brand: metadata.brand,
        color: metadata.color,
        size: metadata.size,
        condition: "used",
        material: metadata.fabric,
        weight_kg: Number(metadata.weight),
        price: Number(metadata.price),
        image_url: preview,
        source_platform: "lens",
      });

      onListingSaved(
        {
          ...metadata,
          id: savedProduct.product_id,
          product_id: savedProduct.product_id,
          preview: savedProduct.image_url,
          water_saved_liters: savedProduct.water_saved_liters,
          weight_kg: savedProduct.weight_kg,
        },
        savedProduct.water_saved_liters || 0
      );
      setStep(1);
      setPreview(null);
    } catch (err) {
      console.error("Save error:", err);
      alert(`Backend'e kaydedilemedi: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (step === 2)
    return (
      <div style={styles.formScroll}>
        <img src={preview} style={styles.formImg} alt="Preview" />
        <h3 style={{ textAlign: "center" }}>Item Details</h3>

        <label style={styles.label}>Item Title</label>
        <input
          type="text"
          placeholder="e.g. Black Velvet Jacket"
          value={metadata.title}
          onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
          style={styles.input}
        />

        <label style={styles.label}>Price (TL)</label>
        <input
          type="number"
          placeholder="2000"
          value={metadata.price}
          onChange={(e) => setMetadata({ ...metadata, price: e.target.value })}
          style={styles.input}
        />

        <label style={styles.label}>Category</label>
        <select
          value={metadata.category}
          onChange={(e) => setMetadata({ ...metadata, category: e.target.value })}
          style={styles.input}
        >
          <option value="tops">Tops</option>
          <option value="pants">Pants</option>
          <option value="shorts">Shorts</option>
          <option value="skirts">Skirts</option>
          <option value="dresses">Dresses</option>
          <option value="shoes">Shoes</option>
          <option value="bags">Bags</option>
          <option value="outerwear">Outerwear</option>
        </select>

        <div style={styles.row}>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Brand</label>
            <input
              type="text"
              placeholder="e.g. BDG"
              value={metadata.brand}
              onChange={(e) =>
                setMetadata({ ...metadata, brand: e.target.value })
              }
              style={styles.input}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Size</label>
            <input
              type="text"
              placeholder="e.g. M / 38"
              value={metadata.size}
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
              value={metadata.color}
              onChange={(e) =>
                setMetadata({ ...metadata, color: e.target.value })
              }
              style={styles.input}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Gender</label>
            <select
              value={metadata.gender}
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
          value={metadata.fabric}
          onChange={(e) => setMetadata({ ...metadata, fabric: e.target.value })}
          style={styles.input}
        >
          <option value="100% Denim">100% Denim</option>
          <option value="100% Cotton">100% Cotton</option>
          <option value="100% Polyester">100% Polyester</option>
          <option value="50% Cotton, 50% Polyester">50% Cotton, 50% Polyester</option>
          <option value="80% Cotton, 20% Polyester">80% Cotton, 20% Polyester</option>
          <option value="Faux leather">Faux leather</option>
          <option value="Canvas">Canvas</option>
          <option value="Recycled polyester">Recycled polyester</option>
        </select>

        <label style={styles.label}>Weight (kg)</label>
        <input
          type="number"
          min="0.1"
          step="0.1"
          value={metadata.weight}
          onChange={(e) => setMetadata({ ...metadata, weight: e.target.value })}
          style={styles.input}
        />

        <button
          onClick={handleSaveListing}
          disabled={isSaving || !metadata.title || !metadata.price || !metadata.weight}
          style={{
            ...styles.primaryBtn,
            opacity: isSaving || !metadata.title || !metadata.price || !metadata.weight ? 0.6 : 1,
          }}
        >
          {isSaving ? "Saving..." : "Confirm & List"}
        </button>
      </div>
    );

  return (
    <div style={{ textAlign: "center", paddingTop: "100px" }}>
      <label style={styles.uploadBtn}>
        Upload Photo
        <input type="file" accept="image/*" onChange={handleUpload} style={{ display: "none" }} />
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
