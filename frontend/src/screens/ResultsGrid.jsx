import React, { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
import { getProducts } from "../api/api";

const ResultsGrid = ({ onProductSelect }) => {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    getProducts()
      .then((data) => {
        setProducts(data);
        setStatus("ready");
      })
      .catch((err) => {
        console.error("API error:", err);
        setError(err.message);
        setStatus("error");
      });
  }, []);

  if (status === "loading") {
    return <p style={{ textAlign: "center", padding: "20px" }}>Loading products...</p>;
  }

  if (status === "error") {
    return (
      <p style={{ color: "#b00020", textAlign: "center", padding: "20px" }}>
        Backend connection failed: {error}
      </p>
    );
  }

  if (products.length === 0) {
    return <p style={{ textAlign: "center", padding: "20px" }}>No products yet.</p>;
  }

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      {products.map((product) => (
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
  );
};

export default ResultsGrid;
