import React, { useState } from "react";
import { analyzeItemImage, createProduct, getToken } from "../api/api";

const FABRIC_OPTIONS = [
  "Denim",
  "Cotton",
  "Polyester",
  "Recycled polyester",
  "Canvas",
  "Faux leather",
  "Leather",
  "Cotton blend",
  "Synthetic",
];

const MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/heic",
  "image/heif",
]);
const ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".heic", ".heif"];

const LensTab = ({ onListingSaved, onAuthRequired }) => {
  const [preview, setPreview] = useState(null);
  const [step, setStep] = useState(1);
  const [isSaving, setIsSaving] = useState(false);
  const [fabricRows, setFabricRows] = useState([
    { material: "Denim", percent: "100" },
  ]);
  const [analysisStatus, setAnalysisStatus] = useState("idle");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState("");
  const [metadata, setMetadata] = useState({
    title: "",
    category: "tops",
    brand: "",
    size: "M",
    color: "",
    gender: "Unisex",
    fabric: "Denim",
    weight: 0.5,
    pattern: "",
    price: "",
  });

  const fabricTotal = fabricRows.reduce(
    (total, row) => total + Number(row.percent || 0),
    0
  );
  const hasValidFabricRows =
    fabricRows.length > 0 &&
    fabricRows.every((row) => row.material && Number(row.percent) > 0) &&
    fabricTotal === 100;

  const buildFabricComposition = () =>
    fabricRows
      .map((row) => `${Number(row.percent)}% ${row.material}`)
      .join(", ");

  const updateFabricRow = (index, field, value) => {
    setFabricRows((currentRows) =>
      currentRows.map((row, rowIndex) =>
        rowIndex === index ? { ...row, [field]: value } : row
      )
    );
  };

  const addFabricRow = () => {
    setFabricRows((currentRows) => [
      ...currentRows,
      { material: "Cotton", percent: "" },
    ]);
  };

  const removeFabricRow = (index) => {
    setFabricRows((currentRows) =>
      currentRows.length === 1
        ? currentRows
        : currentRows.filter((_, rowIndex) => rowIndex !== index)
    );
  };

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = "";

    if (!isAllowedImage(file)) {
      alert("Please upload a JPEG, PNG, or HEIC image.");
      return;
    }

    if (file.size > MAX_IMAGE_SIZE_BYTES) {
      alert("Image must be 5MB or smaller.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setPreview(reader.result);
      setStep(2);
    };
    reader.readAsDataURL(file);
    runItemAnalysis(file);
  };

  const handleBackToUpload = () => {
    if (isSaving) return;
    setPreview(null);
    setStep(1);
    setAnalysisStatus("idle");
    setAnalysisResult(null);
    setAnalysisError("");
  };

  const runItemAnalysis = async (file) => {
    setAnalysisStatus("loading");
    setAnalysisResult(null);
    setAnalysisError("");

    try {
      const result = await analyzeItemImage(file);
      setAnalysisResult(result);

      if (!result.is_fashion) {
        setAnalysisStatus("rejected");
        setAnalysisError(result.rejected_reason || "This image does not look like a fashion item.");
        return;
      }

      setMetadata((currentMetadata) => ({
        ...currentMetadata,
        category: result.category || currentMetadata.category,
        color: result.color || currentMetadata.color,
        pattern: result.pattern || currentMetadata.pattern,
        weight: result.weight_kg || currentMetadata.weight,
      }));
      if (result.material) {
        setFabricRows([{ material: result.material, percent: "100" }]);
      }
      setAnalysisStatus("ready");
    } catch (err) {
      setAnalysisStatus("error");
      setAnalysisError(err.message || "AI analysis could not run.");
    }
  };

  const handleSaveListing = async () => {
    if (!getToken()) {
      alert("Ilan kaydetmek icin once Profile sekmesinden giris yapmalisin.");
      onAuthRequired?.();
      return;
    }

    setIsSaving(true);

    try {
      const fabricComposition = buildFabricComposition();
      const savedProduct = await createProduct({
        title: metadata.title,
        description: metadata.pattern
          ? `${metadata.title} | Pattern: ${metadata.pattern}`
          : metadata.title,
        category: metadata.category,
        subcategory: metadata.gender,
        brand: metadata.brand,
        color: metadata.color,
        size: metadata.size,
        condition: "used",
        material: fabricComposition,
        weight_kg: Number(metadata.weight),
        price: Number(metadata.price),
        image_url: preview,
        source_platform: "lens",
      });

      onListingSaved(
        {
          ...metadata,
          fabric: fabricComposition,
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
        <button
          type="button"
          onClick={handleBackToUpload}
          disabled={isSaving}
          style={{
            ...styles.backBtn,
            opacity: isSaving ? 0.5 : 1,
          }}
        >
          Back
        </button>
        <img src={preview} style={styles.formImg} alt="Preview" />
        <h3 style={{ textAlign: "center" }}>Item Details</h3>
        {analysisStatus !== "idle" && (
          <div
            style={{
              ...styles.analysisBox,
              ...(analysisStatus === "rejected" ? styles.analysisRejected : {}),
            }}
          >
            {analysisStatus === "loading" && "AI is analyzing the image..."}
            {analysisStatus === "ready" && analysisResult && (
              <>
                <strong>AI suggestions applied.</strong>
                <span>
                  {analysisResult.category} | {analysisResult.color} | {analysisResult.pattern}
                </span>
                <span>
                  Category confidence: {Math.round((analysisResult.category_confidence || 0) * 100)}%
                </span>
              </>
            )}
            {analysisStatus === "rejected" && analysisError}
            {analysisStatus === "error" && `AI analysis unavailable: ${analysisError}`}
          </div>
        )}

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

        <label style={styles.label}>Pattern</label>
        <input
          type="text"
          placeholder="e.g. Solid / Striped / Denim"
          value={metadata.pattern}
          onChange={(e) => setMetadata({ ...metadata, pattern: e.target.value })}
          style={styles.input}
        />

        <label style={styles.label}>Fabric (for Water Impact)</label>
        <div style={styles.fabricBox}>
          {fabricRows.map((row, index) => (
            <div key={index} style={styles.fabricRow}>
              <select
                value={row.material}
                onChange={(e) =>
                  updateFabricRow(index, "material", e.target.value)
                }
                style={styles.fabricSelect}
              >
                {FABRIC_OPTIONS.map((fabric) => (
                  <option key={fabric} value={fabric}>
                    {fabric}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="1"
                max="100"
                step="1"
                placeholder="%"
                value={row.percent}
                onChange={(e) =>
                  updateFabricRow(index, "percent", e.target.value)
                }
                style={styles.percentInput}
              />
              <button
                type="button"
                onClick={() => removeFabricRow(index)}
                disabled={fabricRows.length === 1}
                style={{
                  ...styles.removeFabricBtn,
                  opacity: fabricRows.length === 1 ? 0.4 : 1,
                }}
                aria-label="Remove fabric"
                title="Remove fabric"
              >
                -
              </button>
            </div>
          ))}
          <div style={styles.fabricFooter}>
            <button
              type="button"
              onClick={addFabricRow}
              style={styles.addFabricBtn}
            >
              Add Fabric
            </button>
            <span
              style={{
                ...styles.fabricTotal,
                color: fabricTotal === 100 ? "#2d5a27" : "#b45309",
              }}
            >
              Total: {fabricTotal || 0}%
            </span>
          </div>
        </div>

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
          disabled={
            isSaving ||
            !metadata.title ||
            !metadata.price ||
            !hasValidFabricRows ||
            !metadata.weight ||
            analysisStatus === "rejected"
          }
          style={{
            ...styles.primaryBtn,
            opacity:
              isSaving ||
              !metadata.title ||
              !metadata.price ||
              !hasValidFabricRows ||
              !metadata.weight ||
              analysisStatus === "rejected"
                ? 0.6
                : 1,
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
        <input
          type="file"
          accept="image/jpeg,image/png,image/heic,image/heif"
          onChange={handleUpload}
          style={{ display: "none" }}
        />
      </label>
    </div>
  );
};

function isAllowedImage(file) {
  const typeAllowed = ALLOWED_IMAGE_TYPES.has(file.type);
  const lowerName = file.name.toLowerCase();
  const extensionAllowed = ALLOWED_IMAGE_EXTENSIONS.some((extension) =>
    lowerName.endsWith(extension)
  );
  return typeAllowed || extensionAllowed;
}

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
  backBtn: {
    alignSelf: "flex-start",
    background: "white",
    border: "1px solid #2d5a27",
    borderRadius: "20px",
    color: "#2d5a27",
    cursor: "pointer",
    fontWeight: "bold",
    padding: "8px 14px",
  },
  row: { display: "flex", gap: "10px" },
  label: { fontSize: "12px", fontWeight: "bold", color: "#666" },
  analysisBox: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    borderRadius: "10px",
    color: "#2d5a27",
    fontSize: "12px",
    padding: "10px",
  },
  analysisRejected: {
    background: "#fff7ed",
    border: "1px solid #fed7aa",
    color: "#9a3412",
  },
  fabricBox: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  fabricRow: {
    display: "grid",
    gridTemplateColumns: "1fr 74px 38px",
    gap: "8px",
    alignItems: "center",
  },
  fabricSelect: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    width: "100%",
    boxSizing: "border-box",
    background: "white",
  },
  percentInput: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    width: "100%",
    boxSizing: "border-box",
  },
  removeFabricBtn: {
    height: "38px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    background: "white",
    color: "#666",
    cursor: "pointer",
    fontWeight: "bold",
  },
  fabricFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "10px",
  },
  addFabricBtn: {
    background: "white",
    color: "#2d5a27",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    padding: "9px 12px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  fabricTotal: {
    fontSize: "12px",
    fontWeight: "bold",
  },
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
