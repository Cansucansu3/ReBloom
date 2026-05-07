import React, { useEffect, useRef, useState } from "react";
import LensTab from "./screens/LensTab";
import ResultsGrid from "./screens/ResultsGrid";
import ProfileScreen from "./screens/ProfileScreen";
import ProductDetail from "./screens/ProductDetail";
import HomeScreen from "./screens/HomeScreen";
import OutfitScreen from "./screens/OutfitScreen";
import {
  clearToken,
  getMyProducts,
  getToken,
  recordSearch,
  visualSearchProducts,
} from "./api/api";

function App() {
  useEffect(() => {
    document.title = "ReBloom";
  }, []);

  const [view, setView] = useState("results");
  const [myItems, setMyItems] = useState([]);
  const [totalWaterSaved, setTotalWaterSaved] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [outfitProduct, setOutfitProduct] = useState(null);
  const [visualProducts, setVisualProducts] = useState(null);
  const [visualStatus, setVisualStatus] = useState("idle");
  const [visualError, setVisualError] = useState("");
  const visualInputRef = useRef(null);

  useEffect(() => {
    if (view !== "myItems") return;

    getMyProducts()
      .then((products) => {
        setMyItems(products.map(mapProductToMyItem));
      })
      .catch((err) => {
        setMyItems([]);
        if (err.status === 401) {
          clearToken();
          setView("profile");
        }
      });
  }, [view]);

  const showProfile = () => {
    setSelectedProduct(null);
    setOutfitProduct(null);
    setMyItems([]);
    setView("profile");
  };

  const showMyItems = () => {
    setSelectedProduct(null);
    setOutfitProduct(null);
    if (!getToken()) {
      setMyItems([]);
      setView("profile");
      return;
    }

    setView("myItems");
  };

  const showLens = () => {
    setSelectedProduct(null);
    setOutfitProduct(null);
    setView("lens");
  };

  const handleFinalizeListing = (newItem, savings) => {
    setMyItems((currentItems) => [
      { ...newItem, savings, status: "Active" },
      ...currentItems,
    ]);
    setTotalWaterSaved((current) => current + savings);
    setView("myItems");
  };

  const handleSearch = (event) => {
    event.preventDefault();
    const trimmedSearch = searchTerm.trim();
    setActiveSearch(trimmedSearch);
    setVisualProducts(null);
    setVisualStatus("idle");
    setSelectedProduct(null);
    setView("results");

    if (trimmedSearch) {
      recordSearch(trimmedSearch).catch(() => {});
    }
  };

  const showHome = () => {
    setActiveSearch("");
    setSearchTerm("");
    setVisualProducts(null);
    setVisualStatus("idle");
    setSelectedProduct(null);
    setOutfitProduct(null);
    setView("results");
  };

  const handleVisualSearch = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setActiveSearch("");
    setSearchTerm("");
    setSelectedProduct(null);
    setOutfitProduct(null);
    setVisualProducts([]);
    setVisualError("");
    setVisualStatus("loading");
    setView("results");

    try {
      const data = await visualSearchProducts(file);
      setVisualProducts(data.products || []);
      setVisualStatus("ready");
    } catch (err) {
      setVisualProducts([]);
      setVisualError(err.message);
      setVisualStatus("error");
    }
  };

  const showOutfit = (product) => {
    setSelectedProduct(null);
    setOutfitProduct(product);
  };

  return (
    <div
      className="App"
      style={{ paddingBottom: "80px", fontFamily: "sans-serif" }}
    >
      {outfitProduct ? (
        <OutfitScreen
          item={outfitProduct}
          onBack={() => setOutfitProduct(null)}
          onProductSelect={(product) => {
            setOutfitProduct(null);
            setSelectedProduct(product);
          }}
        />
      ) : selectedProduct ? (
        <ProductDetail
          item={selectedProduct}
          onBack={() => setSelectedProduct(null)}
          onShowOutfit={showOutfit}
        />
      ) : (
        <>
          <header style={styles.header}>
            <h1 style={{ margin: 0 }}>ReBloom</h1>
            <form onSubmit={handleSearch} style={styles.searchContainer}>
              <input
                type="text"
                placeholder="Search styles..."
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                style={styles.searchInput}
              />
              <button type="submit" style={styles.searchBtn}>
                Search
              </button>
              <button
                type="button"
                onClick={() => visualInputRef.current?.click()}
                style={styles.photoSearchBtn}
                aria-label="Search by photo"
                title="Search by photo"
              >
                <span style={styles.cameraIconWrap} aria-hidden="true">
                  <svg
                    viewBox="0 0 32 32"
                    width="24"
                    height="24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M7.5 11.5h3L12.3 8h7.4l1.8 3.5h3a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3h-17a3 3 0 0 1-3-3v-9a3 3 0 0 1 3-3Z" />
                    <circle cx="15.5" cy="18" r="4.7" />
                    <path d="m19 21.5 5 5" />
                    <path d="M21.4 8.7c.4-2.7 2.1-4.5 5.1-5.2.3 2.8-.9 4.8-3.6 6" />
                    <path d="M21.6 8.8c-1.5-2-3.5-2.8-5.9-2.2.9 2.2 2.5 3.3 5 3.4" />
                  </svg>
                </span>
              </button>
              <input
                ref={visualInputRef}
                type="file"
                accept="image/*"
                onChange={handleVisualSearch}
                style={{ display: "none" }}
              />
            </form>
          </header>

          <main>
            {view === "results" && (
              visualStatus !== "idle" ? (
                <ResultsGrid
                  onProductSelect={setSelectedProduct}
                  providedProducts={visualProducts || []}
                  statusOverride={visualStatus}
                  errorOverride={visualError}
                  heading="Visual search results"
                  emptyMessage="No visually similar products found yet."
                />
              ) : activeSearch ? (
                <ResultsGrid
                  onProductSelect={setSelectedProduct}
                  searchQuery={activeSearch}
                />
              ) : (
                <HomeScreen onProductSelect={setSelectedProduct} />
              )
            )}

            {view === "lens" && (
              <LensTab
                onListingSaved={handleFinalizeListing}
                onAuthRequired={() => setView("profile")}
              />
            )}

            {view === "profile" && (
              <ProfileScreen
                totalWaterSaved={totalWaterSaved}
                onAuthChange={() => setMyItems([])}
              />
            )}

            {view === "myItems" && (
              <div style={{ padding: "20px" }}>
                <h2 style={{ textAlign: "center" }}>My Uploaded Items</h2>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "15px",
                    justifyContent: "center",
                  }}
                >
                  {myItems.length === 0 ? (
                    <p>No items listed yet.</p>
                  ) : (
                    myItems.map((item, i) => (
                      <div
                        key={i}
                        style={styles.miniCard}
                        onClick={() => setSelectedProduct(item)}
                      >
                        <img
                          src={item.preview}
                          style={styles.miniImg}
                          alt="item"
                        />
                        <p
                          style={{
                            fontSize: "14px",
                            fontWeight: "bold",
                            margin: "5px 0",
                          }}
                        >
                          {item.title}
                        </p>
                        <p style={{ fontSize: "12px", color: "#666" }}>
                          {item.brand} | {item.size}
                        </p>
                        <span style={styles.statusBadge}>Listing Active</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </main>
        </>
      )}

      <nav style={styles.navBar}>
        <button onClick={showHome} style={styles.navItem}>
          Home
        </button>
        <button onClick={showLens} style={styles.navItem}>
          Lens
        </button>
        <button onClick={showMyItems} style={styles.navItem}>
          My Items
        </button>
        <button onClick={showProfile} style={styles.navItem}>
          Profile
        </button>
      </nav>
    </div>
  );
}

const styles = {
  header: {
    background: "#2d5a27",
    color: "white",
    padding: "15px",
    textAlign: "center",
  },
  searchContainer: {
    display: "flex",
    justifyContent: "center",
    marginTop: "10px",
    gap: "5px",
  },
  searchInput: {
    padding: "8px",
    borderRadius: "20px",
    border: "none",
    width: "70%",
  },
  searchBtn: {
    background: "white",
    border: "none",
    borderRadius: "20px",
    padding: "5px 10px",
    cursor: "pointer",
  },
  photoSearchBtn: {
    width: "38px",
    height: "38px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    background: "white",
    color: "#2d5a27",
    border: "none",
    borderRadius: "50%",
    cursor: "pointer",
    boxShadow: "0 2px 8px rgba(31, 63, 28, 0.18)",
    flex: "0 0 38px",
  },
  cameraIconWrap: {
    position: "relative",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: "24px",
    height: "24px",
  },
  navBar: {
    position: "fixed",
    bottom: 0,
    width: "100%",
    background: "#fff",
    borderTop: "1px solid #eee",
    display: "flex",
    justifyContent: "space-around",
    padding: "10px 0",
  },
  navItem: {
    background: "none",
    border: "none",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  miniCard: {
    border: "1px solid #eee",
    padding: "15px",
    borderRadius: "15px",
    textAlign: "center",
    width: "140px",
    backgroundColor: "white",
    cursor: "pointer",
  },
  miniImg: {
    width: "100%",
    height: "100px",
    objectFit: "cover",
    borderRadius: "10px",
  },
  statusBadge: {
    fontSize: "10px",
    backgroundColor: "#e8f5e9",
    color: "#2d5a27",
    padding: "3px 8px",
    borderRadius: "10px",
    border: "1px solid #2d5a27",
  },
};

export default App;

function mapProductToMyItem(product) {
  return {
    id: product.product_id,
    product_id: product.product_id,
    title: product.title,
    brand: product.brand,
    size: product.size,
    color: product.color,
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
    status: "Active",
  };
}
