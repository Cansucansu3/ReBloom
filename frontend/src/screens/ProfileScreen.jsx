import React, { useEffect, useState } from "react";
import {
  clearToken,
  getLikedProducts,
  getMe,
  getMyImpact,
  getToken,
  login,
  register,
  unlikeProduct,
  updateMe,
} from "../api/api";
import ProductCard from "../components/ProductCard";
import VirtualGardenCard from "../components/VirtualGardenCard";

const ProfileScreen = ({ totalWaterSaved, onAuthChange, onProductSelect }) => {
  const [impactWaterSaved, setImpactWaterSaved] = useState(totalWaterSaved || 0);
  const [impactStats, setImpactStats] = useState({
    total_items_reused: 0,
    virtual_trees: 0,
    real_trees_earned: 0,
    impact_points: 0,
    legacy_certificate: null,
  });
  const [mode, setMode] = useState("login");
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);
  const [impactError, setImpactError] = useState("");
  const [favorites, setFavorites] = useState([]);
  const [favoritesStatus, setFavoritesStatus] = useState("idle");
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");
  const [profileDraft, setProfileDraft] = useState({
    name: "",
    username: "",
    location: "",
    bio: "",
    profile_image: "",
  });
  const [form, setForm] = useState({
    name: "",
    username: "",
    email: "",
    password: "",
    location: "",
  });

  const refreshImpact = async () => {
    try {
      const impact = await getMyImpact();
      setImpactWaterSaved(Math.round(impact.total_water_saved_liters || 0));
      setImpactStats({
        total_items_reused: impact.total_items_reused || 0,
        virtual_trees: impact.virtual_trees || 0,
        real_trees_earned: impact.real_trees_earned || 0,
        impact_points: impact.impact_points || 0,
        legacy_certificate: impact.legacy_certificate || null,
      });
      setImpactError("");
    } catch (err) {
      setImpactWaterSaved(0);
      setImpactStats({
        total_items_reused: 0,
        virtual_trees: 0,
        real_trees_earned: 0,
        impact_points: 0,
        legacy_certificate: null,
      });
      setImpactError("Impact data could not be loaded.");
      if (err.status === 401) {
        throw err;
      }
    }
  };

  const refreshFavorites = async () => {
    setFavoritesStatus("loading");
    try {
      const products = await getLikedProducts();
      setFavorites(products);
      setFavoritesStatus("ready");
    } catch (err) {
      setFavorites([]);
      setFavoritesStatus("error");
      if (err.status === 401) {
        throw err;
      }
    }
  };

  const removeFavorite = async (productId) => {
    try {
      await unlikeProduct(productId);
      setFavorites((current) =>
        current.filter((product) => product.product_id !== productId)
      );
      setFavoritesStatus("ready");
    } catch {
      setFavoritesStatus("error");
    }
  };

  const loadProfile = async () => {
    if (!getToken()) return;

    setProfileLoading(true);
    setError("");

    try {
      const profile = await getMe();
      setUser(profile);
      setProfileDraft({
        name: profile.name || "",
        username: profile.username || "",
        location: profile.location || "",
        bio: profile.bio || "",
        profile_image: profile.profile_image || "",
      });

      try {
        await Promise.all([refreshImpact(), refreshFavorites()]);
      } catch (impactErr) {
        if (impactErr.status === 401) {
          throw impactErr;
        }
      }
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        setUser(null);
        setImpactWaterSaved(0);
      } else {
        setError(err.message || "Profile could not be loaded.");
      }
    } finally {
      setProfileLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      if (mode === "register") {
        await register({
          name: form.name,
          username: form.username,
          email: form.email,
          password: form.password,
          location: form.location || null,
        });
      }

      await login(form.email, form.password);
      await loadProfile();
      onAuthChange?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    clearToken();
    setUser(null);
    setImpactWaterSaved(0);
    setFavorites([]);
    setFavoritesStatus("idle");
    onAuthChange?.();
  };

  const handleProfileImage = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setProfileMessage("Please select a JPEG or PNG profile image.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setProfileMessage("Profile image must be 2MB or smaller.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setProfileDraft((current) => ({
        ...current,
        profile_image: reader.result,
      }));
      setProfileMessage("");
    };
    reader.readAsDataURL(file);
  };

  const saveProfile = async () => {
    setProfileSaving(true);
    setProfileMessage("");
    try {
      const updated = await updateMe(profileDraft);
      setUser(updated);
      setProfileDraft({
        name: updated.name || "",
        username: updated.username || "",
        location: updated.location || "",
        bio: updated.bio || "",
        profile_image: updated.profile_image || "",
      });
      setEditingProfile(false);
      setProfileMessage("Profile updated.");
    } catch (err) {
      setProfileMessage(err.message || "Profile could not be updated.");
    } finally {
      setProfileSaving(false);
    }
  };

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

        {profileLoading && !user ? (
          <p style={{ color: "#666" }}>Loading profile...</p>
        ) : user ? (
          <div style={styles.profileSummary}>
            <div style={styles.profileAvatar}>
              {user.profile_image ? (
                <img src={user.profile_image} alt="" style={styles.profileAvatarImage} />
              ) : (
                getInitial(user.name)
              )}
            </div>
            <div>
              <p style={styles.profileName}>{user.name}</p>
              <p style={styles.profileUsername}>@{user.username}</p>
              <p style={styles.profileEmail}>{user.email}</p>
              {user.location && <p style={styles.profileMeta}>{user.location}</p>}
              {user.bio && <p style={styles.profileBio}>{user.bio}</p>}
            </div>
            <div style={styles.profileActions}>
              <button
                type="button"
                onClick={() => {
                  setEditingProfile((current) => !current);
                  setProfileMessage("");
                }}
                style={styles.secondaryBtn}
              >
                {editingProfile ? "Cancel Edit" : "Edit Profile"}
              </button>
              <button onClick={handleLogout} style={styles.secondaryBtn}>
                Logout
              </button>
            </div>

            {editingProfile && (
              <div style={styles.profileEditor}>
                <div style={styles.editAvatar}>
                  {profileDraft.profile_image ? (
                    <img
                      src={profileDraft.profile_image}
                      alt=""
                      style={styles.profileAvatarImage}
                    />
                  ) : (
                    getInitial(profileDraft.name)
                  )}
                </div>
                <label style={styles.imagePicker}>
                  Change Profile Photo
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    onChange={handleProfileImage}
                    style={styles.hiddenInput}
                  />
                </label>
                {profileDraft.profile_image && (
                  <button
                    type="button"
                    onClick={() =>
                      setProfileDraft((current) => ({
                        ...current,
                        profile_image: "",
                      }))
                    }
                    style={styles.removePhotoButton}
                  >
                    Remove Photo
                  </button>
                )}
                <input
                  placeholder="Name"
                  value={profileDraft.name}
                  onChange={(event) =>
                    setProfileDraft({ ...profileDraft, name: event.target.value })
                  }
                  style={styles.input}
                />
                <input
                  placeholder="Username"
                  value={profileDraft.username}
                  onChange={(event) =>
                    setProfileDraft({ ...profileDraft, username: event.target.value })
                  }
                  style={styles.input}
                />
                <input
                  placeholder="Location"
                  value={profileDraft.location}
                  onChange={(event) =>
                    setProfileDraft({ ...profileDraft, location: event.target.value })
                  }
                  style={styles.input}
                />
                <textarea
                  placeholder="About me"
                  maxLength={500}
                  value={profileDraft.bio}
                  onChange={(event) =>
                    setProfileDraft({ ...profileDraft, bio: event.target.value })
                  }
                  style={styles.bioInput}
                />
                <button
                  type="button"
                  onClick={saveProfile}
                  disabled={profileSaving}
                  style={styles.primaryBtn}
                >
                  {profileSaving ? "Saving..." : "Save Profile"}
                </button>
              </div>
            )}
            {profileMessage && <p style={styles.profileMessage}>{profileMessage}</p>}
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={styles.authForm}>
            <div style={styles.modeRow}>
              <button
                type="button"
                onClick={() => setMode("login")}
                style={mode === "login" ? styles.activeModeBtn : styles.modeBtn}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                style={mode === "register" ? styles.activeModeBtn : styles.modeBtn}
              >
                Register
              </button>
            </div>

            {mode === "register" && (
              <>
                <input
                  placeholder="Name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  style={styles.input}
                />
                <input
                  placeholder="Username"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  style={styles.input}
                  required
                />
                <input
                  placeholder="Location"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  style={styles.input}
                />
              </>
            )}

            <input
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              style={styles.input}
            />
            <input
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              style={styles.input}
            />
            {error && <p style={{ color: "#b00020", margin: 0 }}>{error}</p>}
            <button type="submit" style={styles.primaryBtn}>
              {mode === "login" ? "Login" : "Create Account"}
            </button>
          </form>
        )}

        <div style={{ marginTop: "18px" }}>
          <VirtualGardenCard impact={impactStats} totalWaterSaved={impactWaterSaved} />
        </div>

        {impactError && (
          <p style={{ color: "#8a6d3b", fontSize: "13px", margin: "6px 0 0" }}>
            {impactError}
          </p>
        )}

        {user && (
          <section style={styles.favoritesSection}>
            <h3 style={styles.favoritesTitle}>My Favorites</h3>
            {favoritesStatus === "loading" ? (
              <p style={styles.favoritesMessage}>Loading favorites...</p>
            ) : favoritesStatus === "error" ? (
              <p style={styles.favoritesMessage}>Favorites could not be loaded.</p>
            ) : favorites.length === 0 ? (
              <p style={styles.favoritesMessage}>
                Products you favorite will appear here.
              </p>
            ) : (
              <div style={styles.favoritesGrid}>
                {favorites.map((product) => (
                  <div key={product.product_id} style={styles.favoriteItem}>
                    <ProductCard
                      item={mapProductForCard(product)}
                      onClick={() => onProductSelect?.(mapProductForDetail(product))}
                    />
                    <button
                      type="button"
                      onClick={() => removeFavorite(product.product_id)}
                      style={styles.removeFavoriteButton}
                    >
                      Remove from Favorites
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
};

const styles = {
  profileSummary: {
    display: "grid",
    justifyItems: "center",
    gap: "8px",
    marginBottom: "16px",
  },
  profileAvatar: {
    width: "92px",
    height: "92px",
    borderRadius: "50%",
    background: "#e8f5e9",
    color: "#2d5a27",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    fontSize: "34px",
    fontWeight: "bold",
  },
  profileAvatarImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
  profileName: { margin: "4px 0", fontWeight: "bold", fontSize: "19px" },
  profileUsername: { margin: "4px 0", color: "#2d5a27", fontWeight: "bold" },
  profileEmail: { margin: "4px 0", color: "#666" },
  profileMeta: { margin: "4px 0", color: "#667064" },
  profileBio: {
    maxWidth: "520px",
    margin: "8px auto 0",
    color: "#4f5c4e",
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
  },
  profileActions: { display: "flex", gap: "8px", justifyContent: "center" },
  profileEditor: {
    width: "min(100%, 480px)",
    display: "grid",
    gap: "10px",
    marginTop: "10px",
    padding: "14px",
    border: "1px solid #dceadc",
    borderRadius: "10px",
    boxSizing: "border-box",
  },
  editAvatar: {
    width: "84px",
    height: "84px",
    margin: "0 auto",
    borderRadius: "50%",
    overflow: "hidden",
    background: "#e8f5e9",
    color: "#2d5a27",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: "bold",
    fontSize: "30px",
  },
  imagePicker: {
    padding: "9px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    color: "#2d5a27",
    cursor: "pointer",
    fontWeight: "bold",
  },
  hiddenInput: { display: "none" },
  removePhotoButton: {
    border: 0,
    background: "transparent",
    color: "#8f2d24",
    cursor: "pointer",
    fontWeight: "bold",
  },
  bioInput: {
    minHeight: "100px",
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    resize: "vertical",
    fontFamily: "inherit",
  },
  profileMessage: { color: "#2d5a27", fontWeight: "bold", margin: "4px 0" },
  authForm: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    margin: "0 auto 16px",
    maxWidth: "320px",
  },
  modeRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
  },
  modeBtn: {
    padding: "10px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    background: "white",
    color: "#2d5a27",
    cursor: "pointer",
  },
  activeModeBtn: {
    padding: "10px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    background: "#2d5a27",
    color: "white",
    cursor: "pointer",
  },
  input: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ddd",
  },
  primaryBtn: {
    background: "#2d5a27",
    color: "white",
    padding: "12px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  secondaryBtn: {
    background: "white",
    color: "#2d5a27",
    padding: "8px 12px",
    border: "1px solid #2d5a27",
    borderRadius: "8px",
    cursor: "pointer",
  },
  favoritesSection: {
    marginTop: "22px",
    paddingTop: "18px",
    borderTop: "1px solid #dceadc",
  },
  favoritesTitle: {
    margin: "0 0 8px",
    color: "#1f3f1c",
  },
  favoritesMessage: {
    color: "#667064",
    margin: "10px 0",
  },
  favoritesGrid: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
  },
  favoriteItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    width: "200px",
    marginBottom: "10px",
  },
  removeFavoriteButton: {
    margin: "-4px 10px 0",
    padding: "8px",
    border: "1px solid #8f2d24",
    borderRadius: "8px",
    background: "white",
    color: "#8f2d24",
    cursor: "pointer",
    fontWeight: "bold",
  },
  gardenCard: {
    marginTop: "18px",
    background: "#f8faf8",
    border: "1px solid #dceadc",
    borderRadius: "18px",
    padding: "18px",
  },
  treeImageWrap: {
    width: "190px",
    height: "190px",
    margin: "0 auto 8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  treeImage: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
  },
  stageEyebrow: {
    margin: "4px 0 2px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  stageTitle: {
    margin: "0",
    color: "#1f3f1c",
    fontSize: "26px",
  },
  stageCopy: {
    margin: "6px 0 14px",
    color: "#5f6f5e",
    fontSize: "14px",
  },
  progressTrack: {
    height: "18px",
    width: "100%",
    backgroundColor: "#e5ece4",
    borderRadius: "999px",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#4f8f45",
    borderRadius: "999px",
    transition: "width 0.5s",
  },
  progressLabel: {
    margin: "10px 0 2px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  progressText: {
    fontWeight: "bold",
    color: "#4f4a5f",
    margin: "0 0 4px",
  },
  totalWaterText: {
    color: "#2d5a27",
    fontWeight: "bold",
    margin: "0 0 14px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
    gap: "8px",
  },
  statBox: {
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "12px",
    padding: "10px 6px",
    display: "grid",
    gap: "3px",
    color: "#2d5a27",
  },
  gardenStrip: {
    marginTop: "14px",
    display: "grid",
    gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
    gap: "8px",
  },
  gardenLevelText: {
    gridColumn: "1 / -1",
    margin: "0 0 4px",
    color: "#2d5a27",
    fontSize: "13px",
    fontWeight: "bold",
  },
  gardenPlot: {
    minHeight: "58px",
    borderRadius: "14px",
    background: "#edf4ec",
    border: "1px dashed #bdd7ba",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  gardenPlotFilled: {
    minHeight: "58px",
    borderRadius: "14px",
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  gardenTree: {
    width: "48px",
    height: "48px",
    objectFit: "contain",
  },
  emptyPlotDot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    background: "#bdd7ba",
  },
};

export default ProfileScreen;

function getInitial(name) {
  return String(name || "R").trim().charAt(0).toUpperCase();
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
    gender: product.gender,
    occasion: product.occasion,
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
