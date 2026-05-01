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

  if (displayStatus === "loading") {
    return <p style={{ textAlign: "center", padding: "20px" }}>Loading products...</p>;
  }

  if (displayStatus === "error") {
    return (
      <p style={{ color: "#b00020", textAlign: "center", padding: "20px" }}>
        Backend connection failed: {displayError}
      </p>
    );
  }

  if (visibleProducts.length === 0) {
    return (
      <p style={{ textAlign: "center", padding: "20px" }}>
        {emptyMessage || (searchQuery ? `No products found for "${searchQuery}".` : "No products yet.")}
      </p>
    );
  }

  return (
    <>
      {heading && <h2 style={{ margin: "20px", color: "#1f3f1c" }}>{heading}</h2>}
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
              weight: product.is_second_hand ? "Second-hand" : "New",
              image: product.image_url,
            })
          }
          item={{
            id: product.product_id,
            title: product.title,
            price: product.price,
            fabric: product.brand || product.category,
            weight: product.is_second_hand ? "Second-hand" : "New",
            image: product.image_url,
          }}
        />
      ))}
    </div>
    </>
  );
};

export default ResultsGrid;
