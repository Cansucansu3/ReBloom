import React, { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import {
  getMe,
  getProducts,
  getPublicUserProfile,
  searchProfiles,
} from "../api/api";

const productMatchesSearch = (product, searchQuery) => {
  if (!searchQuery) return true;

  const normalizedQuery = searchQuery.toLowerCase();
  const searchableValues = [
    product.title,
    product.description,
    product.brand,
    product.category,
    product.subcategory,
    product.occasion,
    product.material,
    product.color,
    product.size,
  ];

  return searchableValues.some((value) =>
    String(value || "").toLowerCase().includes(normalizedQuery)
  );
};

const ResultsGrid = ({
  onProductSelect,
  onProfileSelect,
  onOwnProfileSelect,
  searchQuery,
  providedProducts,
  statusOverride,
  errorOverride,
  heading,
  emptyMessage,
  queryImagePreview,
}) => {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [people, setPeople] = useState([]);
  const [peopleStatus, setPeopleStatus] = useState("idle");
  const [profileLoadingId, setProfileLoadingId] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const useProvidedProducts = Array.isArray(providedProducts);

  useEffect(() => {
    if (useProvidedProducts) return;

    setStatus("loading");
    getProducts({ query: searchQuery })
      .then((data) => {
        setProducts(data);
        setStatus("ready");
      })
      .catch((err) => {
        console.error("API error:", err);
        setError(err.message);
        setStatus("error");
      });
  }, [searchQuery, useProvidedProducts]);

  useEffect(() => {
    if (useProvidedProducts || !searchQuery?.trim()) {
      setPeople([]);
      setPeopleStatus("idle");
      return;
    }

    let mounted = true;
    setPeopleStatus("loading");
    searchProfiles(searchQuery)
      .then((data) => {
        if (!mounted) return;
        setPeople(data);
        setPeopleStatus("ready");
      })
      .catch(() => {
        if (!mounted) return;
        setPeople([]);
        setPeopleStatus("error");
      });

    return () => {
      mounted = false;
    };
  }, [searchQuery, useProvidedProducts]);

  useEffect(() => {
    if (useProvidedProducts || !searchQuery?.trim()) return;

    let mounted = true;
    getMe()
      .then((user) => {
        if (mounted) setCurrentUserId(user.user_id);
      })
      .catch(() => {
        if (mounted) setCurrentUserId(null);
      });

    return () => {
      mounted = false;
    };
  }, [searchQuery, useProvidedProducts]);

  const openProfile = async (person) => {
    if (person.user_id === currentUserId && onOwnProfileSelect) {
      onOwnProfileSelect();
      return;
    }

    if (!onProfileSelect) return;

    setProfileLoadingId(person.user_id);
    try {
      const profile = await getPublicUserProfile(person.user_id);
      onProfileSelect(profile);
    } catch {
      setPeopleStatus("error");
    } finally {
      setProfileLoadingId(null);
    }
  };

  const sourceProducts = useProvidedProducts ? providedProducts : products;
  const displayStatus = statusOverride || status;
  const displayError = errorOverride || error;

  const visibleProducts = sourceProducts.filter((product) =>
    productMatchesSearch(product, searchQuery)
  );
  const resultsHeader = (
    <>
      {queryImagePreview && (
        <div style={styles.queryPreview}>
          <img
            src={queryImagePreview}
            alt="Searched item"
            style={styles.queryPreviewImage}
          />
          <div>
            <p style={styles.queryPreviewLabel}>Searched image</p>
            <p style={styles.queryPreviewText}>Showing visually similar items</p>
          </div>
        </div>
      )}
      {heading && <h2 style={styles.heading}>{heading}</h2>}
    </>
  );

  if (displayStatus === "loading") {
    return (
      <>
        {resultsHeader}
        <p style={{ textAlign: "center", padding: "20px" }}>Loading products...</p>
      </>
    );
  }

  if (displayStatus === "error") {
    return (
      <>
        {resultsHeader}
        <p style={{ color: "#b00020", textAlign: "center", padding: "20px" }}>
          Backend connection failed: {displayError}
        </p>
      </>
    );
  }

  if (
    visibleProducts.length === 0 &&
    people.length === 0 &&
    peopleStatus !== "loading"
  ) {
    return (
      <>
        {resultsHeader}
        <p style={{ textAlign: "center", padding: "20px" }}>
          {emptyMessage || (searchQuery ? `No products found for "${searchQuery}".` : "No products yet.")}
        </p>
      </>
    );
  }

  return (
    <>
      {resultsHeader}
      {!useProvidedProducts && searchQuery && (
        <section style={styles.peopleSection}>
          <h2 style={styles.sectionHeading}>People</h2>
          {peopleStatus === "loading" ? (
            <p style={styles.peopleMessage}>Searching profiles...</p>
          ) : people.length > 0 ? (
            <div style={styles.peopleGrid}>
              {people.map((person) => {
                const isCurrentUser = person.user_id === currentUserId;

                return (
                  <button
                    key={person.user_id}
                    type="button"
                    onClick={() => openProfile(person)}
                    disabled={profileLoadingId === person.user_id}
                    style={{
                      ...styles.personCard,
                      ...(isCurrentUser ? styles.currentUserCard : {}),
                    }}
                  >
                    <span style={styles.avatar}>
                      {person.profile_image ? (
                        <img
                          src={person.profile_image}
                          alt=""
                          style={styles.avatarImage}
                        />
                      ) : (
                        getInitial(person.name)
                      )}
                    </span>
                    <span style={styles.personDetails}>
                      <span style={styles.personTitleRow}>
                        <strong style={styles.personName}>{person.name}</strong>
                        {isCurrentUser && <span style={styles.youBadge}>You</span>}
                      </span>
                      <span style={styles.personUsername}>@{person.username}</span>
                      <span style={styles.personMeta}>
                        {person.active_listing_count} listings
                        {" | "}
                        {person.virtual_trees} trees
                        {person.location ? ` | ${person.location}` : ""}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <p style={styles.peopleMessage}>No matching profiles.</p>
          )}
        </section>
      )}
      {visibleProducts.length > 0 && (
        <h2 style={styles.sectionHeading}>Products</h2>
      )}
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      {visibleProducts.map((product) => (
        <ProductCard
          key={product.product_id}
          onClick={() =>
            onProductSelect({
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
              gender: product.gender,
              occasion: product.occasion,
              color: product.color,
              condition: product.condition,
              material: product.material,
              fabric: product.material || product.brand || product.category,
              weight: product.weight_kg,
              weight_kg: product.weight_kg,
              water_saved_liters: product.water_saved_liters,
              image: product.image_url,
            })
          }
          item={{
            id: product.product_id,
            title: product.title,
            price: product.price,
            fabric: product.material || product.brand || product.category,
            weight: product.weight_kg,
            waterSaved: product.water_saved_liters,
            image: product.image_url,
          }}
        />
      ))}
    </div>
    </>
  );
};

const styles = {
  sectionHeading: {
    margin: "18px 20px 8px",
    color: "#1f3f1c",
    textAlign: "center",
    fontSize: "22px",
  },
  peopleSection: {
    maxWidth: "980px",
    margin: "0 auto",
    padding: "0 20px",
  },
  peopleGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "10px",
  },
  personCard: {
    minHeight: "88px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    border: "1px solid #d8e8d4",
    borderRadius: "8px",
    padding: "12px",
    background: "#f8fbf7",
    color: "#1f3f1c",
    textAlign: "left",
    cursor: "pointer",
  },
  currentUserCard: {
    borderColor: "#73a66d",
    background: "#f1f8ef",
  },
  avatar: {
    width: "48px",
    height: "48px",
    flex: "0 0 48px",
    borderRadius: "50%",
    background: "#e4f2e2",
    display: "grid",
    placeItems: "center",
    fontSize: "20px",
    fontWeight: "bold",
    overflow: "hidden",
  },
  avatarImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
  personDetails: {
    minWidth: 0,
    display: "grid",
    gap: "2px",
  },
  personTitleRow: {
    minWidth: 0,
    display: "flex",
    alignItems: "center",
    gap: "7px",
  },
  personName: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  youBadge: {
    flex: "0 0 auto",
    padding: "2px 7px",
    borderRadius: "999px",
    background: "#2d6729",
    color: "white",
    fontSize: "11px",
    fontWeight: "bold",
  },
  personUsername: {
    color: "#2d5a27",
    fontSize: "13px",
    fontWeight: "bold",
  },
  personMeta: {
    color: "#667064",
    fontSize: "12px",
    lineHeight: 1.35,
  },
  peopleMessage: {
    margin: "8px 0",
    color: "#667064",
    textAlign: "center",
  },
  heading: {
    margin: "16px 20px 8px",
    color: "#1f3f1c",
    textAlign: "center",
  },
  queryPreview: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    maxWidth: "520px",
    margin: "18px auto 8px",
    padding: "12px",
    border: "1px solid #d8e8d4",
    borderRadius: "12px",
    background: "#f6fbf5",
    boxSizing: "border-box",
  },
  queryPreviewImage: {
    width: "78px",
    height: "78px",
    objectFit: "cover",
    borderRadius: "10px",
    background: "white",
  },
  queryPreviewLabel: {
    margin: "0 0 4px",
    color: "#1f3f1c",
    fontWeight: "bold",
  },
  queryPreviewText: {
    margin: 0,
    color: "#666",
    fontSize: "13px",
  },
};

export default ResultsGrid;

function getInitial(name) {
  return String(name || "R").trim().charAt(0).toUpperCase();
}
