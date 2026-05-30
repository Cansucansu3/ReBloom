import React, { useEffect, useState } from "react";
import {
  checkoutCart,
  clearToken,
  getCart,
  getMyOrders,
  removeFromCart,
} from "../api/api";

const CartScreen = ({ onAuthRequired, onProductSelect }) => {
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState("cart");
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(null);

  const loadCart = async () => {
    setStatus("loading");
    setMessage("");

    try {
      const data = await getCart();
      setCart({
        items: data.items || [],
        total: Number(data.total || 0),
      });
      setStatus("ready");
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        onAuthRequired?.();
        return;
      }

      setMessage(err.message || "Could not load cart.");
      setStatus("error");
    }
  };

  const loadOrders = async () => {
    try {
      const data = await getMyOrders();
      setOrders(data || []);
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        onAuthRequired?.();
      }
    }
  };

  useEffect(() => {
    loadCart();
    loadOrders();
  }, []);

  const handleRemove = async (cartId) => {
    setMessage("");

    try {
      await removeFromCart(cartId);
      setCart((current) => {
        const removedItem = current.items.find((item) => item.cart_id === cartId);
        return {
          items: current.items.filter((item) => item.cart_id !== cartId),
          total: Math.max(0, current.total - Number(removedItem?.price || 0)),
        };
      });
    } catch (err) {
      setMessage(err.message || "Could not remove item.");
    }
  };

  const handleCheckout = async (sellerId) => {
    setMessage("");
    setCheckoutLoading(sellerId);

    try {
      const result = await checkoutCart(sellerId);
      await loadCart();
      await loadOrders();
      setMessage(
        `Order completed. ${Math.round(
          Number(result.water_saved_liters || 0)
        ).toLocaleString()} L saved.`
      );
      setActiveTab("orders");
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        onAuthRequired?.();
        return;
      }

      if (err.status === 409) {
        await loadCart();
      }

      setMessage(err.message || "Checkout could not be completed.");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const totalWaterSaved = cart.items.reduce(
    (sum, item) => sum + Number(item.water_saved_liters || 0),
    0
  );

  const hasItems = cart.items.length > 0;
  const sellerGroups = groupCartItemsBySeller(cart.items);

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h2 style={styles.title}>Cart</h2>
        <button onClick={loadCart} style={styles.refreshButton}>
          Refresh
        </button>
      </header>

      <div style={styles.tabRow}>
        <button
          type="button"
          onClick={() => setActiveTab("cart")}
          style={activeTab === "cart" ? styles.activeTabBtn : styles.tabBtn}
        >
          Cart ({cart.items.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("orders")}
          style={activeTab === "orders" ? styles.activeTabBtn : styles.tabBtn}
        >
          My Orders ({orders.length})
        </button>
      </div>

      {activeTab === "cart" && status === "loading" && (
        <p style={styles.statusText}>Loading cart...</p>
      )}

      {activeTab === "cart" && status === "error" && (
        <p style={{ ...styles.statusText, color: "#b00020" }}>{message}</p>
      )}

      {activeTab === "cart" && status === "ready" && !hasItems && (
        <div style={styles.emptyState}>
          <h3 style={styles.emptyTitle}>Your cart is empty</h3>
          <p style={styles.emptyCopy}>Add an item from product detail to see it here.</p>
        </div>
      )}

      {activeTab === "cart" && status === "ready" && hasItems && (
        <>
          <section style={styles.summary}>
            <div>
              <p style={styles.summaryLabel}>Total</p>
              <h3 style={styles.summaryValue}>
                {Number(cart.total).toLocaleString()} TL
              </h3>
            </div>
            <div style={styles.summaryDivider} />
            <div>
              <p style={styles.summaryLabel}>Water saved</p>
              <h3 style={styles.summaryValue}>
                {Math.round(totalWaterSaved).toLocaleString()} L
              </h3>
            </div>
          </section>

          <section style={styles.sellerGroups}>
            {sellerGroups.map((group) => (
              <article key={group.sellerId} style={styles.sellerBlock}>
                <div style={styles.sellerHeader}>
                  <div>
                    <p style={styles.summaryLabel}>Seller</p>
                    <h3 style={styles.sellerTitle}>{group.sellerName}</h3>
                  </div>
                  <div style={styles.sellerTotals}>
                    <strong>{group.items.length} item{group.items.length > 1 ? "s" : ""}</strong>
                    <span>{Number(group.total).toLocaleString()} TL</span>
                    <span>{Math.round(group.waterSaved).toLocaleString()} L saved</span>
                  </div>
                </div>

                <div style={styles.list}>
                  {group.items.map((item) => (
                    <div key={item.cart_id} style={styles.cartItem}>
                      <button
                        type="button"
                        onClick={() => onProductSelect?.(mapCartItemToProduct(item))}
                        style={styles.itemButton}
                      >
                        <img
                          src={item.image_url}
                          alt={item.title}
                          style={styles.itemImage}
                        />
                        <div style={styles.itemInfo}>
                          <h3 style={styles.itemTitle}>{item.title}</h3>
                          <p style={styles.itemMeta}>
                            {item.brand || "ReBloom"} {item.size ? `| ${item.size}` : ""}
                          </p>
                          <p style={styles.waterText}>
                            {Math.round(Number(item.water_saved_liters || 0)).toLocaleString()} L saved
                          </p>
                        </div>
                        <strong style={styles.price}>{Number(item.price).toLocaleString()} TL</strong>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleRemove(item.cart_id)}
                        style={styles.removeButton}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => handleCheckout(group.sellerId)}
                  style={styles.checkoutButton}
                  disabled={checkoutLoading === group.sellerId}
                >
                  {checkoutLoading === group.sellerId
                    ? "Processing..."
                    : `Complete purchase from ${group.sellerName}`}
                </button>
              </article>
            ))}
          </section>

          {message && <p style={styles.message}>{message}</p>}
        </>
      )}

      {activeTab === "orders" && (
        <section style={styles.orderList}>
          {orders.length === 0 ? (
            <div style={styles.emptyState}>
              <h3 style={styles.emptyTitle}>No orders yet</h3>
              <p style={styles.emptyCopy}>Completed purchases will appear here.</p>
            </div>
          ) : (
            orders.map((order) => (
              <article key={order.order_id} style={styles.orderItem}>
                <button
                  type="button"
                  onClick={() => onProductSelect?.(mapOrderToProduct(order))}
                  style={styles.itemButton}
                >
                  <img
                    src={order.product?.image_url}
                    alt={order.product?.title}
                    style={styles.itemImage}
                  />
                  <div style={styles.itemInfo}>
                    <h3 style={styles.itemTitle}>{order.product?.title}</h3>
                    <p style={styles.itemMeta}>
                      Seller: {order.seller_name || "ReBloom seller"}
                    </p>
                    <p style={styles.waterText}>
                      {Math.round(
                        Number(order.product?.water_saved_liters || 0)
                      ).toLocaleString()} L saved
                    </p>
                  </div>
                  <strong style={styles.price}>
                    {Number(order.price).toLocaleString()} TL
                  </strong>
                </button>
                <div style={styles.orderMeta}>
                  <span style={styles.statusBadge}>{order.status}</span>
                  <span>
                    {order.ordered_at
                      ? new Date(order.ordered_at).toLocaleDateString()
                      : ""}
                  </span>
                </div>
              </article>
            ))
          )}

          {message && <p style={styles.message}>{message}</p>}
        </section>
      )}
    </div>
  );
};

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f8faf8",
    padding: "18px 16px 100px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "16px",
  },
  title: {
    margin: 0,
    color: "#1f3f1c",
    fontSize: "28px",
  },
  refreshButton: {
    border: "1px solid #2d5a27",
    background: "white",
    color: "#2d5a27",
    borderRadius: "20px",
    padding: "8px 14px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  tabRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
    marginBottom: "16px",
  },
  tabBtn: {
    border: "1px solid #d6ddd5",
    background: "white",
    color: "#2d5a27",
    borderRadius: "20px",
    padding: "10px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  activeTabBtn: {
    border: "1px solid #2d5a27",
    background: "#2d5a27",
    color: "white",
    borderRadius: "20px",
    padding: "10px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  statusText: {
    textAlign: "center",
    color: "#555",
    marginTop: "48px",
  },
  emptyState: {
    background: "white",
    border: "1px solid #e0e8df",
    borderRadius: "12px",
    padding: "28px",
    textAlign: "center",
    marginTop: "40px",
  },
  emptyTitle: {
    margin: "0 0 8px",
    color: "#1f3f1c",
  },
  emptyCopy: {
    color: "#666",
    margin: 0,
  },
  list: {
    display: "grid",
    gap: "10px",
  },
  cartItem: {
    background: "#fbfdfb",
    border: "1px solid #e0e8df",
    borderRadius: "12px",
    padding: "12px",
  },
  itemButton: {
    width: "100%",
    display: "grid",
    gridTemplateColumns: "78px 1fr auto",
    gap: "12px",
    alignItems: "center",
    border: "none",
    background: "transparent",
    padding: 0,
    textAlign: "left",
    cursor: "pointer",
  },
  itemImage: {
    width: "78px",
    height: "78px",
    objectFit: "contain",
    borderRadius: "10px",
    background: "#f4f7f4",
  },
  itemInfo: {
    minWidth: 0,
  },
  itemTitle: {
    margin: "0 0 5px",
    color: "#4f4a5f",
    fontSize: "16px",
  },
  itemMeta: {
    margin: "0 0 7px",
    color: "#777",
    fontSize: "13px",
  },
  waterText: {
    margin: 0,
    color: "#2d5a27",
    fontSize: "13px",
    fontWeight: "bold",
  },
  price: {
    color: "#1f3f1c",
    fontSize: "16px",
    whiteSpace: "nowrap",
  },
  removeButton: {
    width: "100%",
    marginTop: "10px",
    border: "1px solid #d6ddd5",
    background: "#fff",
    color: "#8a2f2f",
    borderRadius: "20px",
    padding: "9px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  summary: {
    display: "grid",
    gridTemplateColumns: "1fr auto 1fr",
    alignItems: "center",
    gap: "16px",
    marginTop: "18px",
    padding: "18px",
    background: "#e8f5e9",
    border: "1px solid #c8e6c9",
    borderRadius: "12px",
  },
  summaryDivider: {
    width: "1px",
    height: "42px",
    background: "#b8d9bb",
  },
  summaryLabel: {
    margin: "0 0 5px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  summaryValue: {
    margin: 0,
    color: "#1f3f1c",
    fontSize: "21px",
  },
  message: {
    textAlign: "center",
    color: "#8a2f2f",
    fontSize: "14px",
  },
  sellerGroups: {
    marginTop: "16px",
    display: "grid",
    gap: "14px",
  },
  sellerBlock: {
    background: "white",
    border: "1px solid #e0e8df",
    borderRadius: "12px",
    padding: "14px",
  },
  sellerHeader: {
    display: "grid",
    gridTemplateColumns: "1fr auto",
    gap: "12px",
    alignItems: "start",
    paddingBottom: "12px",
    borderBottom: "1px solid #eef2ed",
    marginBottom: "12px",
  },
  sellerTitle: {
    margin: 0,
    color: "#1f3f1c",
    fontSize: "22px",
  },
  sellerTotals: {
    display: "grid",
    gap: "3px",
    textAlign: "right",
    color: "#4f4a5f",
    fontSize: "13px",
  },
  checkoutButton: {
    width: "100%",
    marginTop: "12px",
    border: "none",
    background: "#2d5a27",
    color: "white",
    borderRadius: "20px",
    padding: "10px 14px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  orderList: {
    display: "grid",
    gap: "12px",
  },
  orderItem: {
    background: "white",
    border: "1px solid #e0e8df",
    borderRadius: "12px",
    padding: "12px",
  },
  orderMeta: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "10px",
    color: "#777",
    fontSize: "13px",
  },
  statusBadge: {
    background: "#e8f5e9",
    color: "#2d5a27",
    border: "1px solid #c8e6c9",
    borderRadius: "999px",
    padding: "4px 10px",
    fontWeight: "bold",
    textTransform: "capitalize",
  },
};

function mapCartItemToProduct(item) {
  return {
    id: item.product_id,
    product_id: item.product_id,
    title: item.title,
    brand: item.brand,
    size: item.size,
    price: item.price,
    image: item.image_url,
    preview: item.image_url,
    water_saved_liters: item.water_saved_liters,
    seller_id: item.seller_id,
    seller_name: item.seller_name,
    is_active: true,
  };
}

function mapOrderToProduct(order) {
  const product = order.product || {};
  return {
    id: product.product_id || order.product_id,
    product_id: product.product_id || order.product_id,
    title: product.title,
    brand: product.brand,
    size: product.size,
    color: product.color,
    category: product.category,
    price: order.price,
    image: product.image_url,
    preview: product.image_url,
    water_saved_liters: product.water_saved_liters,
    seller_id: order.seller_id,
    seller_name: order.seller_name,
    is_active: false,
    status: "Sold",
  };
}

function groupCartItemsBySeller(items) {
  const groups = new Map();

  items.forEach((item) => {
    const sellerId = item.seller_id || 0;
    const current = groups.get(sellerId) || {
      sellerId,
      sellerName: item.seller_name || "ReBloom seller",
      items: [],
      total: 0,
      waterSaved: 0,
    };

    current.items.push(item);
    current.total += Number(item.price || 0);
    current.waterSaved += Number(item.water_saved_liters || 0);
    groups.set(sellerId, current);
  });

  return Array.from(groups.values());
}

export default CartScreen;
