import React from "react";
import ProductCard from "../components/ProductCard";

const ResultsGrid = () => {
  const dummyResults = [
    {
      id: 1,
      title: "Vintage Levi's",
      price: 650,
      fabric: "Denim",
      weight: 0.8,
      image:
        "https://images.unsplash.com/photo-1542272604-787c3835535d?q=80&w=400",
    },
    {
      id: 2,
      title: "Cotton Tee",
      price: 180,
      fabric: "Cotton",
      weight: 0.2,
      image:
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?q=80&w=400",
    },
  ];

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      {dummyResults.map((product) => (
        <ProductCard key={product.id} item={product} />
      ))}
    </div>
  );
};

export default ResultsGrid;
