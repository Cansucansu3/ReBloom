import React, { useEffect, useRef, useState } from "react";
import LensTab from "./screens/LensTab";
import ResultsGrid from "./screens/ResultsGrid";
import ProfileScreen from "./screens/ProfileScreen";
import ProductDetail from "./screens/ProductDetail";
import HomeScreen from "./screens/HomeScreen";
import OutfitScreen from "./screens/OutfitScreen";
import { getMyProducts, recordSearch, visualSearchProducts } from "./api/api";

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
      .catch(() => {});
  }, [view]);

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
                style={styles.searchBtn}
              >
                Photo
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
              <ProfileScreen totalWaterSaved={totalWaterSaved} />
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

          <nav style={styles.navBar}>
            <button onClick={showHome} style={styles.navItem}>
              Home
            </button>
            <button onClick={() => setView("lens")} style={styles.navItem}>
              Lens
            </button>
            <button onClick={() => setView("myItems")} style={styles.navItem}>
              My Items
            </button>
            <button onClick={() => setView("profile")} style={styles.navItem}>
              Profile
            </button>
          </nav>
        </>
      )}
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
    status: "Active",
  };
}
