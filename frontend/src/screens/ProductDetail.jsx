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
    <div style={styles.page}>
      <div style={styles.header}>
        <button onClick={onBack} style={styles.backButton}>
          Back
        </button>
        <button onClick={handleAddToCart} style={styles.headerCartButton}>
          Add to Cart
        </button>
      </div>

      <img
        src={item.preview || item.image}
        style={styles.productImage}
        alt={item.title || "Product"}
      />

      <div style={styles.content}>
        <h2 style={styles.title}>{item.title}</h2>
        <p style={styles.brand}>{item.brand}</p>
        <h3 style={styles.price}>{item.price} TL</h3>

        <div style={styles.metadataGrid}>
          <p>
            <strong>Size:</strong> {item.size || "One Size"}
          </p>
          <p>
            <strong>Color:</strong> {item.color || "Unknown"}
          </p>
          <p>
            <strong>Gender:</strong> {item.gender || item.subcategory || "Unisex"}
          </p>
          <p>
            <strong>Material:</strong> {item.material || item.fabric || "Unknown"}
          </p>
        </div>

        <div style={styles.actions}>
          <button onClick={handleLike} style={styles.favoriteButton}>
            Add to Favorites
          </button>
          <button onClick={handleAddToCart} style={styles.cartButton}>
            Add to Cart
          </button>
          <button onClick={() => onShowOutfit?.(item)} style={styles.outfitButton}>
            Complete the Look
          </button>
          {likeMessage && <p style={styles.message}>{likeMessage}</p>}
          {cartMessage && <p style={styles.message}>{cartMessage}</p>}
        </div>
      </div>

      <hr style={styles.divider} />

      <div style={styles.comments}>
        <h3 style={styles.commentTitle}>Comments</h3>
        {comments.length === 0 ? (
          <p style={styles.emptyComment}>No comments yet.</p>
        ) : (
          comments.map((comment, index) => (
            <p key={index} style={styles.comment}>
              <strong>{comment.user}:</strong> {comment.text}
            </p>
          ))
        )}

        <div style={styles.commentForm}>
          <input
            value={newComment}
            onChange={(event) => setNewComment(event.target.value)}
            placeholder="Add a comment..."
            style={styles.commentInput}
          />
          <button onClick={handleAddComment} style={styles.sendButton}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

const styles = {
  page: {
    paddingBottom: "100px",
    backgroundColor: "#fff",
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px",
  },
  backButton: {
    background: "white",
    border: "1px solid #2d5a27",
    borderRadius: "30px",
    color: "#2d5a27",
    cursor: "pointer",
    fontWeight: "bold",
    padding: "12px 16px",
  },
  headerCartButton: {
    flex: 1,
    padding: "15px",
    borderRadius: "30px",
    border: "none",
    background: "#00d285",
    color: "white",
    fontWeight: "bold",
    cursor: "pointer",
  },
  productImage: {
    width: "100%",
    height: "400px",
    objectFit: "cover",
  },
  content: {
    padding: "20px",
  },
  title: {
    margin: "0",
    fontSize: "22px",
  },
  brand: {
    color: "#6200ee",
    fontWeight: "bold",
    fontSize: "16px",
    margin: "5px 0",
  },
  price: {
    fontSize: "26px",
    margin: "10px 0",
    color: "#333",
  },
  metadataGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "15px",
    margin: "20px 0",
    fontSize: "15px",
  },
  actions: {
    display: "grid",
    gap: "10px",
    marginTop: "20px",
  },
  favoriteButton: {
    width: "100%",
    padding: "15px",
    borderRadius: "30px",
    border: "1px solid #2d5a27",
    background: "white",
    color: "#2d5a27",
    fontWeight: "bold",
    fontSize: "16px",
    cursor: "pointer",
  },
  cartButton: {
    width: "100%",
    padding: "15px",
    borderRadius: "30px",
    border: "none",
    background: "#00d285",
    color: "white",
    fontWeight: "bold",
    fontSize: "16px",
    cursor: "pointer",
  },
  outfitButton: {
    width: "100%",
    padding: "15px",
    borderRadius: "30px",
    border: "none",
    background: "#2d5a27",
    color: "white",
    fontWeight: "bold",
    fontSize: "16px",
    cursor: "pointer",
  },
  message: {
    color: "#2d5a27",
    fontSize: "14px",
    textAlign: "center",
  },
  divider: {
    border: "0",
    borderTop: "1px solid #eee",
    margin: "20px 0",
  },
  comments: {
    padding: "0 20px",
  },
  commentTitle: {
    marginBottom: "15px",
  },
  emptyComment: {
    color: "#999",
    fontSize: "14px",
  },
  comment: {
    fontSize: "14px",
    borderBottom: "1px solid #f0f0f0",
    paddingBottom: "8px",
    marginBottom: "8px",
  },
  commentForm: {
    display: "flex",
    gap: "8px",
    marginTop: "15px",
  },
  commentInput: {
    flex: 1,
    padding: "12px",
    borderRadius: "25px",
    border: "1px solid #ddd",
    outline: "none",
  },
  sendButton: {
    padding: "10px 20px",
    background: "#2d5a27",
    color: "white",
    border: "none",
    borderRadius: "25px",
    cursor: "pointer",
  },
};

export default ProductDetail;
