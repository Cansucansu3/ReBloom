import React, { useState, useEffect } from "react";
import LensTab from "./screens/LensTab";
import ResultsGrid from "./screens/ResultsGrid";
import ProfileScreen from "./screens/ProfileScreen";
import ProductDetail from "./screens/ProductDetail"; // 1. IMPORT THE NEW FILE

function App() {
  useEffect(() => {
    document.title = "ReBloom";
  }, []);

  const [view, setView] = useState("lens");
  const [myItems, setMyItems] = useState([]);
  const [totalWaterSaved, setTotalWaterSaved] = useState(0);

  // 2. NEW STATE: Stores the item the user clicked on
  const [selectedProduct, setSelectedProduct] = useState(null);

  const handleFinalizeListing = (newItem, savings) => {
    setMyItems([...myItems, { ...newItem, savings, status: "Active" }]);
    setView("myItems");
  };

  return (
    <div
      className="App"
      style={{ paddingBottom: "80px", fontFamily: "sans-serif" }}
    >
      {/* 3. CONDITIONAL RENDERING: If a product is selected, show the Detail Page */}
      {selectedProduct ? (
        <ProductDetail
          item={selectedProduct}
          onBack={() => setSelectedProduct(null)}
        />
      ) : (
        /* If NO product is selected, show the normal App structure */
        <>
          <header style={styles.header}>
            <h1 style={{ margin: 0 }}>ReBloom</h1>
            <div style={styles.searchContainer}>
              <input
                type="text"
                placeholder="Search styles..."
                style={styles.searchInput}
              />
              <button style={styles.searchBtn}>🔍</button>
            </div>
          </header>

          <main>
            {/* 1. Results View */}
            {view === "results" && (
              <div
                onClick={() =>
                  setSelectedProduct({
                    title: "Sample Item",
                    price: "100",
                    brand: "Sample",
                    image: "https://via.placeholder.com/400",
                  })
                }
              >
                <ResultsGrid />
              </div>
            )}

            {/* 2. Lens/Upload View */}
            {view === "lens" && (
              <LensTab onListingSaved={handleFinalizeListing} />
            )}

            {/* 3. Profile View */}
            {view === "profile" && (
              <ProfileScreen totalWaterSaved={totalWaterSaved} />
            )}

            {/* 4. My Items View - ENSURE THERE IS ONLY ONE OF THESE BLOCKS */}
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
            <button onClick={() => setView("results")} style={styles.navItem}>
              🏠
              <br />
              Home
            </button>
            <button onClick={() => setView("lens")} style={styles.navItem}>
              📸
              <br />
              Lens
            </button>
            <button onClick={() => setView("myItems")} style={styles.navItem}>
              👕
              <br />
              My Items
            </button>
            <button onClick={() => setView("profile")} style={styles.navItem}>
              🌳
              <br />
              Profile
            </button>
          </nav>
        </>
      )}
    </div>
  );
}

// ... styles remain the same
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
