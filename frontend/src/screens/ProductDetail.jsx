import React, { useEffect, useState } from "react";
import { addToCart, likeProduct, recordProductView } from "../api/api";

const ProductDetail = ({ item, onBack, onShowOutfit }) => {
  const [newComment, setNewComment] = useState("");
  const [comments, setComments] = useState([]);
  const [cartMessage, setCartMessage] = useState("");
  const [likeMessage, setLikeMessage] = useState("");

  useEffect(() => {
    const productId = item.product_id || item.id;
    if (!productId) return;

    recordProductView(productId).catch(() => {});
  }, [item.id, item.product_id]);

  const handleAddComment = () => {
    if (newComment.trim()) {
      setComments([
        ...comments,
        { user: "User_" + Math.floor(Math.random() * 100), text: newComment },
      ]);
      setNewComment("");
    }
  };

  const handleAddToCart = async () => {
    try {
      await addToCart(item.product_id || item.id);
      setCartMessage("Added to cart.");
    } catch (err) {
      setCartMessage(`Could not add to cart: ${err.message}`);
    }
  };

  const handleLike = async () => {
    try {
      await likeProduct(item.product_id || item.id);
      setLikeMessage("Added to favorites.");
    } catch (err) {
      setLikeMessage(`Could not add to favorites: ${err.message}`);
    }
  };

  return (
    <div
      style={{
        paddingBottom: "100px",
        backgroundColor: "#fff",
        minHeight: "100vh",
      }}
    >
      {/* Navigation Header */}
      <div style={{ display: "flex", alignItems: "center", padding: "10px" }}>
        <button
          onClick={onBack}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "24px",
          }}
        >
          ←
        </button>
      </div>

      {/* Product Image */}
      <img
        src={item.preview || item.image}
        style={{ width: "100%", height: "400px", objectFit: "cover" }}
        alt="Product"
      />

      <div style={{ padding: "20px" }}>
        {/* Item Metadata Display */}
        <h2 style={{ margin: "0", fontSize: "22px" }}>{item.title}</h2>
        <p
          style={{
            color: "#6200ee",
            fontWeight: "bold",
            fontSize: "16px",
            margin: "5px 0",
          }}
        >
          {item.brand}
        </p>
        <h3 style={{ fontSize: "26px", margin: "10px 0", color: "#333" }}>
          {item.price} TL
        </h3>

        {/* Detailed Filters Display */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "15px",
            margin: "20px 0",
            fontSize: "15px",
          }}
        >
          <p>
            📏 <strong>Size:</strong> {item.size}
          </p>
          <p>
            🎨 <strong>Color:</strong> {item.color}
          </p>
          <p>
            🚻 <strong>Gender:</strong> {item.gender}
          </p>
        </div>

        {/* Action Button - Only Add to Cart remains */}
        <div style={{ display: "grid", gap: "10px", marginTop: "20px" }}>
          <button
            onClick={handleLike}
            style={{
              width: "100%",
              padding: "15px",
              borderRadius: "30px",
              border: "1px solid #2d5a27",
              background: "white",
              color: "#2d5a27",
              fontWeight: "bold",
              fontSize: "16px",
              cursor: "pointer",
            }}
          >
            Add to Favorites
          </button>
          <button
            onClick={handleAddToCart}
            style={{
              width: "100%",
              padding: "15px",
              borderRadius: "30px",
              border: "none",
              background: "#00d285",
              color: "white",
              fontWeight: "bold",
              fontSize: "16px",
              cursor: "pointer",
            }}
          >
            Add to Cart
          </button>
          <button
            onClick={() => onShowOutfit?.(item)}
            style={{
              width: "100%",
              padding: "15px",
              borderRadius: "30px",
              border: "none",
              background: "#2d5a27",
              color: "white",
              fontWeight: "bold",
              fontSize: "16px",
              cursor: "pointer",
            }}
          >
            Complete the Look
          </button>
          {likeMessage && (
            <p style={{ color: "#2d5a27", fontSize: "14px", textAlign: "center" }}>
              {likeMessage}
            </p>
          )}
          {cartMessage && (
            <p style={{ color: "#2d5a27", fontSize: "14px", textAlign: "center" }}>
              {cartMessage}
            </p>
          )}
        </div>
      </div>

      <hr
        style={{ border: "0", borderTop: "1px solid #eee", margin: "20px 0" }}
      />

      {/* User Comments Section */}
      <div style={{ padding: "0 20px" }}>
        <h3 style={{ marginBottom: "15px" }}>Comments</h3>
        {comments.length === 0 ? (
          <p style={{ color: "#999", fontSize: "14px" }}>
            No comments yet. Be the first to comment.
          </p>
        ) : (
          comments.map((c, i) => (
            <p
              key={i}
              style={{
                fontSize: "14px",
                borderBottom: "1px solid #f0f0f0",
                paddingBottom: "8px",
                marginBottom: "8px",
              }}
            >
              <strong>{c.user}:</strong> {c.text}
            </p>
          ))
        )}

        {/* Comment Input */}
        <div style={{ display: "flex", gap: "8px", marginTop: "15px" }}>
          <input
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            style={{
              flex: 1,
              padding: "12px",
              borderRadius: "25px",
              border: "1px solid #ddd",
              outline: "none",
            }}
          />
          <button
            onClick={handleAddComment}
            style={{
              padding: "10px 20px",
              background: "#2d5a27",
              color: "white",
              border: "none",
              borderRadius: "25px",
              cursor: "pointer",
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;
