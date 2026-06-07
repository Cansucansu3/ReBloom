import React, { useEffect, useState } from "react";
import {
  addProductComment,
  addToCart,
  getProductComments,
  likeProduct,
  recordProductView,
} from "../api/api";

const formatGender = (value) => {
  const normalized = String(value || "").trim().toLowerCase();

  if (["men", "man", "male"].includes(normalized)) return "Men";
  if (["women", "woman", "female"].includes(normalized)) return "Women";
  if (normalized === "unisex") return "Unisex";

  return "Unisex";
};

const ProductDetail = ({ item, onBack, onShowOutfit, onSellerSelect }) => {
  const [newComment, setNewComment] = useState("");
  const [comments, setComments] = useState([]);
  const [commentMessage, setCommentMessage] = useState("");
  const [cartMessage, setCartMessage] = useState("");
  const [likeMessage, setLikeMessage] = useState("");
  const rawWaterSaved = item.water_saved_liters ?? item.waterSaved;
  const waterSaved = Number.isFinite(Number(rawWaterSaved))
    ? Math.round(Number(rawWaterSaved))
    : null;
  const materialLabel = item.material || item.fabric || "Unknown";
  const weightLabel = item.weight_kg ?? item.weight;
  const isSold = item.is_active === false || item.status === "Sold";
  const displayGender = formatGender(item.gender);

  useEffect(() => {
    const productId = item.product_id || item.id;
    if (!productId) return;

    recordProductView(productId).catch(() => {});
  }, [item.id, item.product_id]);

  useEffect(() => {
    const productId = item.product_id || item.id;
    if (!productId) return;

    let mounted = true;
    setCommentMessage("");

    getProductComments(productId)
      .then((data) => {
        if (!mounted) return;
        setComments(data || []);
      })
      .catch(() => {
        if (!mounted) return;
        setComments([]);
        setCommentMessage("Comments could not be loaded.");
      });

    return () => {
      mounted = false;
    };
  }, [item.id, item.product_id]);

  const handleAddComment = async () => {
    const text = newComment.trim();
    if (!text) return;

    try {
      const savedComment = await addProductComment(item.product_id || item.id, text);
      setComments((currentComments) => [...currentComments, savedComment]);
      setNewComment("");
      setCommentMessage("");
    } catch (err) {
      setCommentMessage(`Could not add comment: ${err.message}`);
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
      <button type="button" onClick={onBack} style={styles.backButton}>
        Back
      </button>

      <div style={styles.productImageFrame}>
        <img
          src={item.preview || item.image}
          style={styles.productImage}
          alt={item.title || "Product"}
        />
      </div>

      <div style={styles.content}>
        <h2 style={styles.title}>{item.title}</h2>
        <p style={styles.brand}>{item.brand}</p>
        <h3 style={styles.price}>{item.price} TL</h3>
        {isSold && <p style={styles.soldBadge}>Sold</p>}

        <div style={styles.metadataGrid}>
          <p>
            <strong>Size:</strong> {item.size || "One Size"}
          </p>
          <p>
            <strong>Color:</strong> {item.color || "Unknown"}
          </p>
          <p>
            <strong>Gender:</strong> {displayGender}
          </p>
        </div>

        {item.seller_id && (
          <button
            type="button"
            onClick={() => onSellerSelect?.(item.seller_id)}
            style={styles.sellerButton}
          >
            View seller: {item.seller_name || item.sellerName || "ReBloom seller"}
          </button>
        )}

        <div style={styles.impactBox}>
          <p style={styles.impactLabel}>Water impact</p>
          <h3 style={styles.impactValue}>
            {waterSaved !== null ? `${waterSaved.toLocaleString()} L saved` : "Not calculated"}
          </h3>
          <p style={styles.impactDetail}>
            {materialLabel}
            {weightLabel ? ` | ${Number(weightLabel).toFixed(1)} kg` : ""}
          </p>
        </div>

        <div style={styles.actions}>
          <button onClick={handleLike} style={styles.favoriteButton}>
            Add to Favorites
          </button>
          {!isSold && (
            <button onClick={handleAddToCart} style={styles.cartButton}>
              Add to Cart
            </button>
          )}
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
            <p key={comment.comment_id || index} style={styles.comment}>
              <strong>{comment.username || comment.user_name || "ReBloom user"}:</strong>{" "}
              {comment.text}
            </p>
          ))
        )}
        {commentMessage && <p style={styles.commentMessage}>{commentMessage}</p>}

        <div style={styles.commentForm}>
          <input
            value={newComment}
            onChange={(event) => setNewComment(event.target.value)}
            placeholder="Add a comment..."
            style={styles.commentInput}
          />
          <button type="button" onClick={handleAddComment} style={styles.sendButton}>
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
  backButton: {
    margin: "14px 0 10px 16px",
    border: "1px solid #2d5a27",
    background: "white",
    color: "#2d5a27",
    borderRadius: "20px",
    padding: "8px 14px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  productImageFrame: {
    width: "100%",
    height: "400px",
    background: "#f8faf8",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  productImage: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
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
  soldBadge: {
    display: "inline-block",
    background: "#f7eeee",
    color: "#8a2f2f",
    border: "1px solid #8a2f2f",
    borderRadius: "999px",
    padding: "5px 12px",
    margin: "0 0 10px",
    fontWeight: "bold",
    fontSize: "13px",
  },
  metadataGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "15px",
    margin: "20px 0",
    fontSize: "15px",
  },
  impactBox: {
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    borderRadius: "12px",
    padding: "14px",
    margin: "20px 0",
  },
  sellerButton: {
    width: "100%",
    border: "1px solid #dceadc",
    background: "#f8faf8",
    color: "#2d5a27",
    borderRadius: "14px",
    padding: "12px",
    fontWeight: "bold",
    cursor: "pointer",
    marginBottom: "14px",
  },
  impactLabel: {
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    margin: "0 0 6px",
    textTransform: "uppercase",
  },
  impactValue: {
    color: "#1f3f1c",
    fontSize: "24px",
    margin: 0,
  },
  impactDetail: {
    color: "#555",
    fontSize: "13px",
    margin: "6px 0 0",
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
  commentMessage: {
    color: "#8a2f2f",
    fontSize: "13px",
    margin: "8px 0",
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
