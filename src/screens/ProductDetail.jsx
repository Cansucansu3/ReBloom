import React, { useState } from "react";

const ProductDetail = ({ item, onBack }) => {
  const [newComment, setNewComment] = useState("");
  const [comments, setComments] = useState([]);

  const handleAddComment = () => {
    if (newComment.trim()) {
      setComments([
        ...comments,
        { user: "User_" + Math.floor(Math.random() * 100), text: newComment },
      ]);
      setNewComment("");
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
        <div style={{ marginTop: "20px" }}>
          <button
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
            Sepete Ekle
          </button>
        </div>
      </div>

      <hr
        style={{ border: "0", borderTop: "1px solid #eee", margin: "20px 0" }}
      />

      {/* User Comments Section */}
      <div style={{ padding: "0 20px" }}>
        <h3 style={{ marginBottom: "15px" }}>Yorumlar</h3>
        {comments.length === 0 ? (
          <p style={{ color: "#999", fontSize: "14px" }}>
            Henüz yorum yok. İlk yorumu sen yap!
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
            placeholder="Yorum ekle..."
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
