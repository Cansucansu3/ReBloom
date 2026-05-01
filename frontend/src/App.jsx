import React, { useEffect, useState } from "react";
import LensTab from "./screens/LensTab";
import ResultsGrid from "./screens/ResultsGrid";
import ProfileScreen from "./screens/ProfileScreen";
import ProductDetail from "./screens/ProductDetail";

function App() {
  useEffect(() => {
    document.title = "ReBloom";
  }, []);

  const [view, setView] = useState("lens");
  const [myItems, setMyItems] = useState([]);
  const [totalWaterSaved, setTotalWaterSaved] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);

  const handleFinalizeListing = (newItem, savings) => {
    setMyItems([...myItems, { ...newItem, savings, status: "Active" }]);
    setTotalWaterSaved((current) => current + savings);
    setView("myItems");
  };

  const handleSearch = (event) => {
    event.preventDefault();
    setActiveSearch(searchTerm.trim());
    setSelectedProduct(null);
    setView("results");
  };

  return (
    <div
      className="App"
      style={{ paddingBottom: "80px", fontFamily: "sans-serif" }}
    >
      {selectedProduct ? (
        <ProductDetail
          item={selectedProduct}
          onBack={() => setSelectedProduct(null)}
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
            </form>
          </header>

          <main>
            {view === "results" && (
              <ResultsGrid
                onProductSelect={setSelectedProduct}
                searchQuery={activeSearch}
              />
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
            <button onClick={() => setView("results")} style={styles.navItem}>
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
