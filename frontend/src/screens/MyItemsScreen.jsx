import React, { useState } from "react";
import { removeProductFromSale, updateProduct } from "../api/api";

const CATEGORIES = [
  "tops",
  "pants",
  "shorts",
  "skirts",
  "dresses",
  "shoes",
  "bags",
  "outerwear",
];

const MyItemsScreen = ({ items, onItemsChange, onProductSelect }) => {
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState(null);
  const [savingId, setSavingId] = useState(null);
  const [message, setMessage] = useState("");

  const startEdit = (item) => {
    if (item.is_sold) return;
    setEditingId(item.product_id);
    setDraft({
      title: item.title || "",
      description: item.description || "",
      category: item.category || "tops",
      subcategory: item.subcategory || item.category || "",
      brand: item.brand || "",
      color: item.color || "",
      size: item.size || "",
      gender: item.gender || "Unisex",
      occasion: item.occasion || "Casual",
      condition: item.condition || "Used",
      material: item.material || "",
      weight_kg: item.weight_kg ?? "",
      price: item.price ?? "",
      image_url: item.preview || item.image || "",
    });
    setMessage("");
  };

  const updateDraft = (field, value) => {
    setDraft((current) => ({ ...current, [field]: value }));
  };

  const handleImageChange = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!["image/jpeg", "image/png", "image/heic", "image/heif"].includes(file.type)) {
      setMessage("Please select a JPEG, PNG, or HEIC image.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setMessage("Product image must be 5MB or smaller.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => updateDraft("image_url", reader.result);
    reader.readAsDataURL(file);
  };

  const saveEdit = async (productId) => {
    setSavingId(productId);
    setMessage("");
    try {
      const updated = await updateProduct(productId, {
        ...draft,
        weight_kg: Number(draft.weight_kg),
        price: Number(draft.price),
      });
      onItemsChange((current) =>
        current.map((item) =>
          item.product_id === productId ? mapProductToMyItem(updated) : item
        )
      );
      setEditingId(null);
      setDraft(null);
      setMessage("Listing updated.");
    } catch (err) {
      setMessage(err.message || "Listing could not be updated.");
    } finally {
      setSavingId(null);
    }
  };

  const removeFromSale = async (item) => {
    if (!window.confirm(`Remove "${item.title}" from sale?`)) return;

    setSavingId(item.product_id);
    setMessage("");
    try {
      await removeProductFromSale(item.product_id);
      onItemsChange((current) =>
        current.map((currentItem) =>
          currentItem.product_id === item.product_id
            ? { ...currentItem, is_active: false, status: "Inactive" }
            : currentItem
        )
      );
      setMessage("Listing removed from sale.");
    } catch (err) {
      setMessage(err.message || "Listing could not be removed.");
    } finally {
      setSavingId(null);
    }
  };

  const relist = async (item) => {
    setSavingId(item.product_id);
    setMessage("");
    try {
      const updated = await updateProduct(item.product_id, { is_active: true });
      onItemsChange((current) =>
        current.map((currentItem) =>
          currentItem.product_id === item.product_id
            ? mapProductToMyItem(updated)
            : currentItem
        )
      );
      setMessage("Listing is active again.");
    } catch (err) {
      setMessage(err.message || "Listing could not be relisted.");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div style={styles.page}>
      <h2 style={styles.title}>My Uploaded Items</h2>
      {message && <p style={styles.message}>{message}</p>}

      {items.length === 0 ? (
        <p style={styles.empty}>No items listed yet.</p>
      ) : (
        <div style={styles.grid}>
          {items.map((item) => {
            const status = getStatus(item);
            const isBusy = savingId === item.product_id;
            return (
              <article key={item.product_id} style={styles.card}>
                <button
                  type="button"
                  onClick={() => onProductSelect?.(item)}
                  style={styles.productButton}
                >
                  <img src={item.preview} style={styles.image} alt={item.title} />
                  <strong style={styles.itemTitle}>{item.title}</strong>
                  <span style={styles.meta}>
                    {item.brand || "ReBloom"} {item.size ? `| ${item.size}` : ""}
                  </span>
                </button>

                <span style={{ ...styles.badge, ...styles[`${status.toLowerCase()}Badge`] }}>
                  {status}
                </span>

                {!item.is_sold && (
                  <div style={styles.actions}>
                    <button
                      type="button"
                      onClick={() => startEdit(item)}
                      disabled={isBusy}
                      style={styles.editButton}
                    >
                      Edit
                    </button>
                    {item.is_active ? (
                      <button
                        type="button"
                        onClick={() => removeFromSale(item)}
                        disabled={isBusy}
                        style={styles.removeButton}
                      >
                        Remove from Sale
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => relist(item)}
                        disabled={isBusy}
                        style={styles.relistButton}
                      >
                        Relist
                      </button>
                    )}
                  </div>
                )}

                {editingId === item.product_id && draft && (
                  <div style={styles.editor}>
                    <img src={draft.image_url} alt="" style={styles.editPreview} />
                    <label style={styles.fileLabel}>
                      Change photo
                      <input
                        type="file"
                        accept=".jpg,.jpeg,.png,.heic,.heif,image/*"
                        onChange={handleImageChange}
                        style={styles.hiddenInput}
                      />
                    </label>
                    <Field label="Title" value={draft.title} onChange={(value) => updateDraft("title", value)} />
                    <Field label="Description" value={draft.description} onChange={(value) => updateDraft("description", value)} textarea />
                    <label style={styles.label}>
                      Category
                      <select
                        value={draft.category}
                        onChange={(event) => updateDraft("category", event.target.value)}
                        style={styles.input}
                      >
                        {CATEGORIES.map((category) => (
                          <option key={category} value={category}>{category}</option>
                        ))}
                      </select>
                    </label>
                    <div style={styles.twoColumn}>
                      <Field label="Brand" value={draft.brand} onChange={(value) => updateDraft("brand", value)} />
                      <Field label="Size" value={draft.size} onChange={(value) => updateDraft("size", value)} />
                      <Field label="Color" value={draft.color} onChange={(value) => updateDraft("color", value)} />
                      <Field label="Gender" value={draft.gender} onChange={(value) => updateDraft("gender", value)} />
                      <Field label="Occasion" value={draft.occasion} onChange={(value) => updateDraft("occasion", value)} />
                      <Field label="Condition" value={draft.condition} onChange={(value) => updateDraft("condition", value)} />
                      <Field label="Fabric" value={draft.material} onChange={(value) => updateDraft("material", value)} />
                      <Field label="Weight (kg)" value={draft.weight_kg} onChange={(value) => updateDraft("weight_kg", value)} type="number" />
                      <Field label="Price (TL)" value={draft.price} onChange={(value) => updateDraft("price", value)} type="number" />
                    </div>
                    <div style={styles.editorActions}>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(null);
                          setDraft(null);
                        }}
                        style={styles.cancelButton}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => saveEdit(item.product_id)}
                        disabled={isBusy}
                        style={styles.saveButton}
                      >
                        {isBusy ? "Saving..." : "Save Changes"}
                      </button>
                    </div>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};

function Field({ label, value, onChange, type = "text", textarea = false }) {
  const Component = textarea ? "textarea" : "input";
  return (
    <label style={styles.label}>
      {label}
      <Component
        type={textarea ? undefined : type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={textarea ? styles.textarea : styles.input}
      />
    </label>
  );
}

function getStatus(item) {
  if (item.is_sold) return "Sold";
  return item.is_active ? "Active" : "Inactive";
}

function mapProductToMyItem(product) {
  return {
    id: product.product_id,
    product_id: product.product_id,
    seller_id: product.seller_id,
    seller_name: product.seller_name,
    title: product.title,
    description: product.description,
    brand: product.brand,
    size: product.size,
    gender: product.gender,
    occasion: product.occasion,
    color: product.color,
    condition: product.condition,
    price: product.price,
    preview: product.image_url,
    image: product.image_url,
    category: product.category,
    subcategory: product.subcategory,
    material: product.material,
    fabric: product.material,
    weight: product.weight_kg,
    weight_kg: product.weight_kg,
    water_saved_liters: product.water_saved_liters,
    is_active: product.is_active,
    is_sold: product.is_sold,
    status: getStatus(product),
  };
}

const styles = {
  page: { padding: "20px 16px 100px" },
  title: { textAlign: "center", color: "#173d1b" },
  message: { textAlign: "center", color: "#2d5a27", fontWeight: "bold" },
  empty: { textAlign: "center", color: "#667064" },
  grid: { display: "flex", flexWrap: "wrap", gap: "16px", justifyContent: "center" },
  card: {
    width: "min(100%, 330px)",
    border: "1px solid #dceadc",
    borderRadius: "10px",
    padding: "12px",
    background: "white",
  },
  productButton: {
    border: 0,
    background: "transparent",
    width: "100%",
    cursor: "pointer",
    display: "grid",
    gap: "7px",
    textAlign: "center",
  },
  image: { width: "100%", height: "190px", objectFit: "contain", background: "#f8faf8" },
  itemTitle: { color: "#625b70", fontSize: "16px" },
  meta: { color: "#667064", fontSize: "13px" },
  badge: {
    display: "block",
    width: "fit-content",
    margin: "10px auto",
    padding: "4px 10px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: "bold",
  },
  activeBadge: { color: "#27632a", background: "#e8f5e9" },
  inactiveBadge: { color: "#6a5c20", background: "#fff8dd" },
  soldBadge: { color: "#8a2f2f", background: "#f7eeee" },
  actions: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" },
  editButton: {
    border: "1px solid #2d5a27",
    color: "#2d5a27",
    background: "white",
    padding: "9px",
    borderRadius: "8px",
    cursor: "pointer",
  },
  removeButton: {
    border: "1px solid #8f2d24",
    color: "#8f2d24",
    background: "white",
    padding: "9px",
    borderRadius: "8px",
    cursor: "pointer",
  },
  relistButton: {
    border: "1px solid #2d5a27",
    color: "white",
    background: "#2d5a27",
    padding: "9px",
    borderRadius: "8px",
    cursor: "pointer",
  },
  editor: {
    marginTop: "12px",
    paddingTop: "12px",
    borderTop: "1px solid #dceadc",
    display: "grid",
    gap: "10px",
  },
  editPreview: { width: "100%", height: "150px", objectFit: "contain", background: "#f8faf8" },
  fileLabel: {
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    padding: "9px",
    textAlign: "center",
    color: "#2d5a27",
    cursor: "pointer",
    fontWeight: "bold",
  },
  hiddenInput: { display: "none" },
  label: { display: "grid", gap: "5px", color: "#4f4a5f", fontSize: "13px", fontWeight: "bold" },
  input: { width: "100%", boxSizing: "border-box", padding: "9px", border: "1px solid #ccd8cc", borderRadius: "7px" },
  textarea: { width: "100%", minHeight: "72px", boxSizing: "border-box", padding: "9px", border: "1px solid #ccd8cc", borderRadius: "7px", resize: "vertical" },
  twoColumn: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "9px" },
  editorActions: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" },
  cancelButton: { padding: "10px", border: "1px solid #777", background: "white", borderRadius: "8px", cursor: "pointer" },
  saveButton: { padding: "10px", border: 0, background: "#2d5a27", color: "white", borderRadius: "8px", cursor: "pointer", fontWeight: "bold" },
};

export default MyItemsScreen;
