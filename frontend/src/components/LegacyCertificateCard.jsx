import { LEGACY_GOAL_LITERS } from "../utils/gamificationLogic";

const LegacyCertificateCard = ({ certificate, totalWaterSaved = 0 }) => {
  const saved = Math.max(0, Number(totalWaterSaved || 0));
  const remaining = Math.max(0, LEGACY_GOAL_LITERS - saved);
  const progress = Math.min((saved / LEGACY_GOAL_LITERS) * 100, 100);

  if (!certificate) {
    return (
      <section style={styles.card}>
        <p style={styles.eyebrow}>Legacy Protocol</p>
        <h3 style={styles.title}>Certificate unlocks at 100,000 L</h3>
        <p style={styles.copy}>
          Save {Math.round(remaining).toLocaleString()} L more to generate a ReBloom
          legacy certificate.
        </p>
        <div style={styles.track}>
          <div style={{ ...styles.fill, width: `${Math.max(4, progress)}%` }} />
        </div>
      </section>
    );
  }

  return (
    <section style={styles.card}>
      <p style={styles.eyebrow}>Legacy Certificate</p>
      <h3 style={styles.title}>Real-world impact recorded</h3>
      <div style={styles.grid}>
        <Info label="Certificate ID" value={shortId(certificate.certificate_id)} />
        <Info label="Status" value={formatStatus(certificate.status)} />
        <Info
          label="Total saved"
          value={`${Math.round(
            Number(certificate.total_water_saved_liters || totalWaterSaved || 0)
          ).toLocaleString()} L`}
        />
        <Info label="Location" value={certificate.planting_location || "Demo forest"} />
      </div>
      <p style={styles.hash}>Hash: {certificate.certificate_hash}</p>
      {certificate.gps_location && <p style={styles.hash}>GPS: {certificate.gps_location}</p>}
    </section>
  );
};

function Info({ label, value }) {
  return (
    <div style={styles.info}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function shortId(value) {
  const text = String(value || "");
  return text ? text.slice(0, 8).toUpperCase() : "PENDING";
}

function formatStatus(value) {
  return String(value || "generated").replace(/_/g, " ");
}

const styles = {
  card: {
    marginTop: "14px",
    background: "#f2f8f1",
    border: "1px solid #c8e6c9",
    borderRadius: "16px",
    padding: "14px",
    color: "#1f3f1c",
  },
  eyebrow: {
    margin: "0 0 4px",
    color: "#2d5a27",
    fontSize: "12px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  title: {
    margin: "0 0 8px",
    fontSize: "20px",
  },
  copy: {
    margin: "0 0 10px",
    color: "#5f6f5e",
    fontSize: "14px",
  },
  track: {
    height: "12px",
    borderRadius: "999px",
    background: "#dfeadf",
    overflow: "hidden",
  },
  fill: {
    height: "100%",
    borderRadius: "999px",
    background: "#4f8f45",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
    gap: "8px",
  },
  info: {
    background: "white",
    border: "1px solid #dceadc",
    borderRadius: "12px",
    padding: "9px",
    display: "grid",
    gap: "3px",
  },
  hash: {
    margin: "9px 0 0",
    color: "#5f6f5e",
    fontSize: "12px",
    overflowWrap: "anywhere",
  },
};

export default LegacyCertificateCard;
