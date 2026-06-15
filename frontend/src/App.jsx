import React, { useEffect, useRef, useState } from "react";
import LensTab from "./screens/LensTab";
import ResultsGrid from "./screens/ResultsGrid";
import ProfileScreen from "./screens/ProfileScreen";
import ProductDetail from "./screens/ProductDetail";
import HomeScreen from "./screens/HomeScreen";
import OutfitScreen from "./screens/OutfitScreen";
import CartScreen from "./screens/CartScreen";
import GardenScreen from "./screens/GardenScreen";
import SellerProfileScreen from "./screens/SellerProfileScreen";
import MyItemsScreen from "./screens/MyItemsScreen";
import rebloomMark from "./assets/rebloom-mark.png";
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
  const [selectedSellerProfile, setSelectedSellerProfile] = useState(null);
  const [selectedSellerId, setSelectedSellerId] = useState(null);
  const [productReturnTarget, setProductReturnTarget] = useState(null);
  const [visualProducts, setVisualProducts] = useState(null);
  const [visualStatus, setVisualStatus] = useState("idle");
  const [visualError, setVisualError] = useState("");
  const [visualQueryImage, setVisualQueryImage] = useState("");
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

  useEffect(() => {
    if (!visualQueryImage.startsWith("blob:")) return undefined;
    return () => URL.revokeObjectURL(visualQueryImage);
  }, [visualQueryImage]);

  const showProfile = () => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    setMyItems([]);
    setView("profile");
  };

  const showMyItems = () => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    if (!getToken()) {
      setMyItems([]);
      setView("profile");
      return;
    }

    setView("myItems");
  };

  const showLens = () => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    setView("lens");
  };

  const showCart = () => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    if (!getToken()) {
      setView("profile");
      return;
    }

    setView("cart");
  };

  const showGarden = () => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    if (!getToken()) {
      setView("profile");
      return;
    }

    setView("garden");
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
    setVisualQueryImage("");
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
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
    setVisualQueryImage("");
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    setView("results");
  };

  const handleVisualSearch = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setActiveSearch("");
    setSearchTerm("");
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    setVisualProducts([]);
    setVisualError("");
    setVisualStatus("loading");
    setVisualQueryImage(URL.createObjectURL(file));
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
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    setOutfitProduct(product);
  };

  const showSellerProfile = (sellerId) => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerProfile(null);
    setSelectedSellerId(sellerId);
  };

  const showPublicProfile = (profile) => {
    setSelectedProduct(null);
    setProductReturnTarget(null);
    setOutfitProduct(null);
    setSelectedSellerId(profile?.seller_id || null);
    setSelectedSellerProfile(profile);
  };

  const closeSellerProfile = () => {
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
  };

  const openProductDetail = (product) => {
    setProductReturnTarget(null);
    setSelectedProduct(product);
  };

  const openProductFromSellerProfile = (product) => {
    setProductReturnTarget({
      profile: selectedSellerProfile,
      sellerId: selectedSellerId || selectedSellerProfile?.seller_id || product?.seller_id || null,
    });
    setSelectedSellerProfile(null);
    setSelectedSellerId(null);
    setSelectedProduct(product);
  };

  const openProductFromOutfit = (product) => {
    setProductReturnTarget({
      outfitProduct,
    });
    setOutfitProduct(null);
    setSelectedProduct(product);
  };

  const closeProductDetail = () => {
    const target = productReturnTarget;
    setSelectedProduct(null);
    setProductReturnTarget(null);

    if (target?.outfitProduct) {
      setOutfitProduct(target.outfitProduct);
      return;
    }

    if (target?.profile || target?.sellerId) {
      setSelectedSellerProfile(target.profile || null);
      setSelectedSellerId(target.sellerId || target.profile?.seller_id || null);
    }
  };

  const getNavItemStyle = (targetView) => ({
    ...styles.navItem,
    ...(view === targetView ? styles.navItemActive : {}),
  });

  return (
    <div
      className="App"
      style={{ paddingBottom: "80px", fontFamily: "sans-serif" }}
    >
      {selectedSellerProfile || selectedSellerId ? (
        <SellerProfileScreen
          profile={selectedSellerProfile}
          sellerId={selectedSellerId}
          onBack={closeSellerProfile}
          onProductSelect={openProductFromSellerProfile}
        />
      ) : outfitProduct ? (
        <OutfitScreen
          item={outfitProduct}
          onBack={() => setOutfitProduct(null)}
          onProductSelect={openProductFromOutfit}
        />
      ) : selectedProduct ? (
        <ProductDetail
          item={selectedProduct}
          onBack={closeProductDetail}
          onShowOutfit={showOutfit}
          onSellerSelect={showSellerProfile}
        />
      ) : (
        <>
          <header style={styles.header}>
            <h1 style={styles.logoTitle}>
              <img src={rebloomMark} alt="" style={styles.logoMark} />
              <span>ReBloom</span>
            </h1>
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
                  onProductSelect={openProductDetail}
                  providedProducts={visualProducts || []}
                  statusOverride={visualStatus}
                  errorOverride={visualError}
                  heading="Visual search results"
                  emptyMessage="No visually similar products found yet."
                  queryImagePreview={visualQueryImage}
                />
              ) : activeSearch ? (
                <ResultsGrid
                  onProductSelect={openProductDetail}
                  onProfileSelect={showPublicProfile}
                  onOwnProfileSelect={showProfile}
                  searchQuery={activeSearch}
                />
              ) : (
                <HomeScreen onProductSelect={openProductDetail} />
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
                onProductSelect={openProductDetail}
              />
            )}

            {view === "garden" && (
              <GardenScreen
                onAuthRequired={() => setView("profile")}
                onSellerProfileSelect={showPublicProfile}
              />
            )}

            {view === "cart" && (
              <CartScreen
                onAuthRequired={() => setView("profile")}
                onProductSelect={openProductDetail}
              />
            )}

            {view === "myItems" && (
              <MyItemsScreen
                items={myItems}
                onItemsChange={setMyItems}
                onProductSelect={openProductDetail}
              />
            )}
          </main>
        </>
      )}

      <nav style={styles.navBar}>
        <button onClick={showHome} style={getNavItemStyle("results")}>
          Home
        </button>
        <button onClick={showLens} style={getNavItemStyle("lens")}>
          Lens
        </button>
        <button onClick={showMyItems} style={getNavItemStyle("myItems")}>
          My Items
        </button>
        <button onClick={showCart} style={getNavItemStyle("cart")}>
          Cart
        </button>
        <button onClick={showGarden} style={getNavItemStyle("garden")}>
          Garden
        </button>
        <button onClick={showProfile} style={getNavItemStyle("profile")}>
          Profile
        </button>
      </nav>
    </div>
  );
}

const styles = {
  header: {
    background:
      "linear-gradient(180deg, #2f682d 0%, #245a24 68%, #214f20 100%)",
    color: "white",
    padding: "10px 14px 16px",
    textAlign: "center",
    boxShadow: "0 10px 24px rgba(31, 63, 28, 0.12)",
  },
  logoTitle: {
    margin: 0,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    color: "#06180b",
    fontSize: "clamp(42px, 7vw, 58px)",
    lineHeight: 0.95,
    fontWeight: 800,
    letterSpacing: "-0.02em",
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    textShadow: "0 1px 0 rgba(255, 255, 255, 0.1)",
  },
  logoMark: {
    width: "48px",
    height: "42px",
    objectFit: "cover",
    objectPosition: "center",
    borderRadius: "14px",
    background: "#fbf7ee",
    boxShadow: "0 6px 14px rgba(12, 40, 18, 0.16)",
  },
  searchContainer: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    margin: "8px auto 0",
    gap: "8px",
    maxWidth: "990px",
  },
  searchInput: {
    padding: "12px 14px",
    borderRadius: "999px",
    border: "none",
    width: "70%",
    minWidth: 0,
    fontSize: "16px",
    boxShadow: "inset 0 0 0 1px rgba(31, 63, 28, 0.05)",
  },
  searchBtn: {
    background: "white",
    border: "none",
    borderRadius: "999px",
    padding: "10px 16px",
    cursor: "pointer",
    fontSize: "15px",
    fontWeight: 650,
    boxShadow: "0 6px 14px rgba(12, 40, 18, 0.12)",
  },
  photoSearchBtn: {
    width: "44px",
    height: "44px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    background: "white",
    color: "#2d5a27",
    border: "none",
    borderRadius: "50%",
    cursor: "pointer",
    boxShadow: "0 6px 14px rgba(12, 40, 18, 0.15)",
    flex: "0 0 44px",
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
    left: "50%",
    transform: "translateX(-50%)",
    bottom: 0,
    width: "min(1126px, 100vw)",
    background: "#fff",
    borderTop: "1px solid #eee",
    display: "flex",
    justifyContent: "space-around",
    padding: "10px 0",
    boxSizing: "border-box",
    zIndex: 1000,
  },
  navItem: {
    backgroundColor: "#f1f1f1",
    border: "none",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    cursor: "pointer",
    borderRadius: "999px",
    padding: "7px 12px",
    transition: "background-color 0.2s ease, color 0.2s ease",
  },
  navItemActive: {
    backgroundColor: "#e8f5e9",
    boxShadow: "inset 0 0 0 1px rgba(45, 90, 39, 0.18)",
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
    objectFit: "contain",
    borderRadius: "10px",
    background: "#f8faf8",
  },
  statusBadge: {
    fontSize: "10px",
    backgroundColor: "#e8f5e9",
    color: "#2d5a27",
    padding: "3px 8px",
    borderRadius: "10px",
    border: "1px solid #2d5a27",
  },
  soldStatusBadge: {
    fontSize: "10px",
    backgroundColor: "#f7eeee",
    color: "#8a2f2f",
    padding: "3px 8px",
    borderRadius: "10px",
    border: "1px solid #8a2f2f",
  },
};

export default App;

function mapProductToMyItem(product) {
  return {
    id: product.product_id,
    product_id: product.product_id,
    seller_id: product.seller_id,
    seller_name: product.seller_name,
    title: product.title,
    brand: product.brand,
    size: product.size,
    gender: product.gender,
    occasion: product.occasion,
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
    is_active: product.is_active,
    is_sold: product.is_sold,
    status: product.is_sold ? "Sold" : product.is_active ? "Active" : "Inactive",
  };
}
