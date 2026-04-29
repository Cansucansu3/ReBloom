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
      image: "https://via.placeholder.com/150",
    },
    {
      id: 2,
      title: "Cotton Tee",
      price: 180,
      fabric: "Cotton",
      weight: 0.2,
      image: "https://via.placeholder.com/150",
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
