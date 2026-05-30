import React, { useEffect, useState } from "react";
import { API_BASE_URL, getPublicSellerProfile } from "../api/api";
import ProductCard from "../components/ProductCard";
import { buildGardenSlots, getGardenLevelInfo } from "../utils/gamificationLogic";

const SellerProfileScreen = ({ profile: initialProfile, sellerId, onBack, onProductSelect }) => {
  const [profile, setProfile] = useState(initialProfile || null);
  const [status, setStatus] = useState(initialProfile ? "ready" : "loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (initialProfile || !sellerId) return;

    let mounted = true;
    setStatus("loading");

    getPublicSellerProfile(sellerId)
      .then((data) => {
        if (!mounted) return;
        setProfile(data);
        setStatus("ready");
      })
      .catch((err) => {
        if (!mounted) return;
        setMessage(err.message || "Seller profile could not be loaded.");
        setStatus("error");
      });

    return () => {
      mounted = false;
    };
  }, [initialProfile, sellerId]);

  if (status === "loading") {
    return <p style={styles.statusText}>Loading seller profile...</p>;
  }

  if (status === "error" || !profile) {
    return (
      <div style={styles.page}>
        <button type="button" onClick={onBack} style={styles.backButton}>
          Back
        </button>
        <p style={{ ...styles.statusText, color: "#b00020" }}>{message}</p>
      </div>
    );
  }

  const products = profile.active_products || [];
  const gardenLevel = getGardenLevelInfo(profile.impact.virtual_trees || 0);
  const gardenSlots = buildGardenSlots(profile.impact.virtual_trees || 0, profile.tree.stage);

  return (
    <div style={styles.page}>
      <button type="button" onClick={onBack} style={styles.backButton}>
        Back
      </button>

      <section style={styles.header}>
        <div style={styles.avatar}>{getInitial(profile.name)}</div>
        <div>
          <h2 style={styles.name}>{profile.name}</h2>
          <p style={styles.handle}>{makeUsername(profile.name)}</p>
          <p style={styles.meta}>
            {profile.verified ? "Verified seller" : "ReBloom seller"}
            {profile.location ? ` | ${profile.location}` : ""}
          </p>
          <p style={styles.meta}>
            {Number(profile.total_sales || 0).toLocaleString()} sales
            {profile.rating ? ` | ${Number(profile.rating).toFixed(1)} rating` : ""}
          </p>
        </div>
      </section>

      <section style={styles.gardenCard}>
        <div style={styles.gardenInfo}>
          <p style={styles.eyebrow}>Public Garden</p>
          <h3 style={styles.stageTitle}>
            {Number(profile.impact.virtual_trees || 0).toLocaleString()} virtual trees grown
          </h3>
          <p style={styles.levelText}>
            Garden Level {gardenLevel.level} | {gardenLevel.completedInLevel} /{" "}
            {gardenLevel.slotCount} trees
          </p>
          <p style={styles.totalWaterText}>
            Total saved:{" "}
            {Math.round(Number(profile.impact.total_water_saved_liters || 0)).toLocaleString()} L
          </p>
          <div style={styles.publicGardenGrid}>
            {gardenSlots.map((slot) => (
              <div key={slot.id} style={slot.filled ? styles.publicPlotFilled : styles.publicPlot}>
                {slot.filled ? (
                  <img
                    src={`${API_BASE_URL}/static/trees/${slot.stage}.png`}
                    alt=""
                    style={styles.publicPlotTree}
                  />
                ) : (
                  <span style={styles.emptyDot} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={styles.statsGrid}>
        <Stat label="Virtual trees" value={profile.impact.virtual_trees} />
        <Stat label="Real trees" value={profile.impact.real_trees_earned} />
        <Stat label="Second-hand buys" value={profile.impact.total_items_reused} />
        <Stat label="Impact points" value={profile.impact.impact_points} />
      </section>

      <section style={styles.productsSection}>
        <h3 style={styles.sectionTitle}>Active Listings</h3>
        {products.length === 0 ? (
          <p style={styles.emptyText}>No active listings right now.</p>
        ) : (
          <div style={styles.productGrid}>
            {products.map((product) => (
              <ProductCard
                key={product.product_id}
                item={mapProductForCard(product)}
                onClick={() => onProductSelect?.(mapProductForDetail(product))}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

function Stat({ label, value }) {
  return (
    <div style={styles.stat}>
      <strong>{Number(value || 0).toLocaleString()}</strong>
      <span>{label}</span>
    </div>
  );
}

function getInitial(name) {
  return String(name || "R").trim().charAt(0).toUpperCase();
}

function makeUsername(name) {
  const slug = String(name || "rebloom-user")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return `@${slug || "rebloom-user"}`;
}

function mapProductForCard(product) {
  return {
    id: product.product_id,
    title: product.title,
    price: product.price,
    fabric: product.material || product.brand || product.category,
    weight: product.weight_kg,
    waterSaved: product.water_saved_liters,
    image: product.image_url,
  };
}

function mapProductForDetail(product) {
  return {
    id: product.product_id,
    product_id: product.product_id,
    seller_id: product.seller_id,
    seller_name: product.seller_name,
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
    weight: product.weight_kg,
    weight_kg: product.weight_kg,
    water_saved_liters: product.water_saved_liters,
    image: product.image_url,
    is_active: product.is_active,
  };
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f8faf8",
    padding: "16px 16px 100px",
  },
  backButton: {
    border: "1px solid #2d5a27",
    background: "white",
    color: "#2d5a27",
    borderRadius: "20px",
    padding: "8px 14px",
    fontWeight: "bold",
    cursor: "pointer",
    marginBottom: "12px",
  },
  statusText: {
    textAlign: "center",
    padding: "40px 16px",
    color: "#555",
  },
  header: {
    display: "grid",
    gridTemplateColumns: "72px 1fr",
    gap: "14px",
    alignItems: "center",
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "18px",
    padding: "16px",
  },
  avatar: {
    width: "72px",
    height: "72px",
    borderRadius: "50%",
    background: "#e8f5e9",
    color: "#2d5a27",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "30px",
    fontWeight: "bold",
  },
  name: {
    margin: "0 0 3px",
    color: "#1f3f1c",
  },
  handle: {
    margin: "0 0 5px",
    color: "#2d5a27",
    fontWeight: "bold",
    fontSize: "14px",
  },
  meta: {
    margin: "3px 0",
    color: "#5f6f5e",
    fontSize: "14px",
  },
  gardenCard: {
    marginTop: "14px",
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "18px",
    padding: "14px",
  },
  gardenInfo: {
    textAlign: "left",
  },
  eyebrow: {
    margin: "0 0 4px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  stageTitle: {
    margin: 0,
    color: "#1f3f1c",
    fontSize: "24px",
  },
  levelText: {
    color: "#4f4a5f",
    fontWeight: "bold",
    margin: "5px 0 0",
    fontSize: "13px",
  },
  totalWaterText: {
    color: "#2d5a27",
    fontWeight: "bold",
    margin: "6px 0 0",
    fontSize: "13px",
  },
  publicGardenGrid: {
    marginTop: "12px",
    display: "grid",
    gridTemplateColumns: "repeat(6, minmax(0, 1fr))",
    gap: "8px",
  },
  publicPlot: {
    minHeight: "58px",
    borderRadius: "14px",
    background: "#edf4ec",
    border: "1px dashed #bdd7ba",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  publicPlotFilled: {
    minHeight: "58px",
    borderRadius: "14px",
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  publicPlotTree: {
    width: "48px",
    height: "48px",
    objectFit: "contain",
  },
  emptyDot: {
    width: "11px",
    height: "11px",
    borderRadius: "50%",
    background: "#bdd7ba",
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
  productsSection: {
    marginTop: "18px",
  },
  sectionTitle: {
    color: "#1f3f1c",
    margin: "0 0 10px",
  },
  productGrid: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
  },
  emptyText: {
    textAlign: "center",
    color: "#666",
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "14px",
    padding: "20px",
  },
};

export default SellerProfileScreen;
