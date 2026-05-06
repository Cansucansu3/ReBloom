import React, { useEffect, useState } from "react";
import { getOutfitRecommendations } from "../api/api";
import ProductCard from "../components/ProductCard";


const toDetailItem = (product) => ({
  id: product.product_id,
  product_id: product.product_id,
  title: product.title,
  description: product.description,
  price: product.price,
  brand: product.brand,
  category: product.category,
  subcategory: product.subcategory,
  size: product.size,
  color: product.color,
  condition: product.condition,
  material: product.material,
  fabric: product.material || product.brand || product.category,
  weight: product.is_second_hand ? "Second-hand" : "New",
  image: product.image_url,
});

const toCardItem = (product) => ({
  id: product.product_id,
  title: product.title,
  price: product.price,
  fabric: product.material || product.brand || product.category,
  weight: product.is_second_hand ? "Second-hand" : "New",
  image: product.image_url,
});

const OutfitScreen = ({ item, onBack, onProductSelect }) => {
  const [status, setStatus] = useState("loading");
  const [products, setProducts] = useState([]);
  const [groups, setGroups] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const productId = item.product_id || item.id;
    if (!productId) return;

    setStatus("loading");
    setGroups([]);
    getOutfitRecommendations(productId)
      .then((data) => {
        setProducts(data.products || []);
        setGroups(
          Object.entries(data.groups || {})
            .map(([key, group]) => ({
              key,
              title: group.title || key,
              products: group.products || [],
            }))
            .filter((group) => group.products.length > 0)
        );
        setStatus("ready");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });
  }, [item.id, item.product_id]);

  return (
    <div style={{ minHeight: "100vh", background: "#fff", paddingBottom: "90px" }}>
      <div style={styles.header}>
        <button onClick={onBack} style={styles.backButton}>Back</button>
        <h1 style={styles.title}>Complete the Look</h1>
      </div>

      <div style={styles.base}>
        <img src={item.preview || item.image} alt={item.title} style={styles.baseImage} />
        <div>
          <p style={styles.eyebrow}>Base item</p>
          <h2 style={styles.baseTitle}>{item.title}</h2>
          <p style={styles.meta}>{item.brand} | {item.color} | {item.size}</p>
        </div>
      </div>

      {status === "loading" && <p style={styles.message}>Loading outfit ideas...</p>}
      {status === "error" && <p style={styles.error}>Could not load outfits: {error}</p>}
      {status === "ready" && groups.length === 0 && products.length === 0 && (
        <p style={styles.message}>No outfit matches found yet.</p>
      )}
      {status === "ready" && groups.length > 0 && (
        <div style={styles.groupWrap}>
          {groups.map((group) => (
            <section key={group.key} style={styles.groupSection}>
              <h2 style={styles.groupTitle}>{group.title}</h2>
              <div style={styles.grid}>
                {group.products.map((product) => (
                  <ProductCard
                    key={product.product_id}
                    item={toCardItem(product)}
                    onClick={() => onProductSelect(toDetailItem(product))}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
      {status === "ready" && groups.length === 0 && products.length > 0 && (
        <div style={styles.grid}>
          {products.map((product) => (
            <ProductCard
              key={product.product_id}
              item={toCardItem(product)}
              onClick={() => onProductSelect(toDetailItem(product))}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "16px",
    borderBottom: "1px solid #eee",
  },
  backButton: {
    border: "none",
    background: "#e8f5e9",
    color: "#2d5a27",
    borderRadius: "20px",
    padding: "8px 14px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  title: {
    margin: 0,
    fontSize: "22px",
  },
  base: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    padding: "16px",
    background: "#f7fbf7",
  },
  baseImage: {
    width: "86px",
    height: "86px",
    objectFit: "cover",
    borderRadius: "10px",
  },
  eyebrow: {
    margin: "0 0 4px",
    color: "#666",
    fontSize: "12px",
    fontWeight: "bold",
  },
  baseTitle: {
    margin: 0,
    fontSize: "18px",
  },
  meta: {
    margin: "6px 0 0",
    color: "#666",
    fontSize: "13px",
  },
  grid: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    padding: "8px 20px 18px",
  },
  groupWrap: {
    paddingTop: "18px",
  },
  groupSection: {
    marginBottom: "14px",
  },
  groupTitle: {
    margin: "0",
    padding: "0 24px",
    color: "#2d5a27",
    fontSize: "18px",
  },
  message: {
    textAlign: "center",
    padding: "20px",
  },
  error: {
    color: "#b00020",
    textAlign: "center",
    padding: "20px",
  },
};

export default OutfitScreen;
