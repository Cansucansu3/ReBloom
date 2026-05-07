import React, { useEffect, useState } from "react";
import {
  getHomeRecommendations,
  getLikedSimilarRecommendations,
  getProducts,
} from "../api/api";
import ProductCard from "../components/ProductCard";


const mapProductForDetail = (product) => ({
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
});

const mapProductForCard = (product) => ({
  id: product.product_id,
  title: product.title,
  price: product.price,
  fabric: product.material || product.brand || product.category,
  weight: product.weight_kg,
  waterSaved: product.water_saved_liters,
  image: product.image_url,
});

const ProductSection = ({ title, products, onProductSelect }) => {
  if (!products.length) return null;

  return (
    <section style={styles.section}>
      <h2 style={styles.sectionTitle}>{title}</h2>
      <div style={styles.row}>
        {products.map((product) => (
          <ProductCard
            key={`${title}-${product.product_id}`}
            item={mapProductForCard(product)}
            onClick={() => onProductSelect(mapProductForDetail(product))}
          />
        ))}
      </div>
    </section>
  );
};

const HomeScreen = ({ onProductSelect }) => {
  const [status, setStatus] = useState("loading");
  const [browsingProducts, setBrowsingProducts] = useState([]);
  const [similarProducts, setSimilarProducts] = useState([]);

  useEffect(() => {
    let isMounted = true;

    async function loadHome() {
      setStatus("loading");

      try {
        const [home, likedSimilar] = await Promise.all([
          getHomeRecommendations(),
          getLikedSimilarRecommendations(),
        ]);

        if (!isMounted) return;

        setBrowsingProducts(home.products || []);
        setSimilarProducts(likedSimilar.products || []);
        setStatus("ready");
      } catch (error) {
        try {
          const products = await getProducts();
          if (!isMounted) return;

          setBrowsingProducts(products);
          setSimilarProducts([]);
          setStatus("ready");
        } catch (fallbackError) {
          if (!isMounted) return;
          console.error("Home load error:", error, fallbackError);
          setStatus("error");
        }
      }
    }

    loadHome();

    return () => {
      isMounted = false;
    };
  }, []);

  if (status === "loading") {
    return <p style={styles.message}>Loading recommendations...</p>;
  }

  if (status === "error") {
    return <p style={styles.error}>Recommendations could not be loaded.</p>;
  }

  return (
    <div style={styles.container}>
      <ProductSection
        title="Inspired by your browsing"
        products={browsingProducts}
        onProductSelect={onProductSelect}
      />
      <ProductSection
        title="Similar to items you liked"
        products={similarProducts}
        onProductSelect={onProductSelect}
      />
    </div>
  );
};

const styles = {
  container: {
    padding: "20px 0",
  },
  section: {
    marginBottom: "24px",
  },
  sectionTitle: {
    fontSize: "20px",
    margin: "0 20px 10px",
    color: "#1f3f1c",
  },
  row: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
  },
  message: {
    textAlign: "center",
    padding: "20px",
  },
  error: {
    color: "#b00020",
    textAlign: "center",
    padding: "20px",
  },
};

export default HomeScreen;
