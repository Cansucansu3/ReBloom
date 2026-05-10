import React, { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import { getProducts } from "../api/api";

const productMatchesSearch = (product, searchQuery) => {
  if (!searchQuery) return true;

  const normalizedQuery = searchQuery.toLowerCase();
  const searchableValues = [
    product.title,
    product.description,
    product.brand,
    product.category,
    product.subcategory,
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

  if (visibleProducts.length === 0) {
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
