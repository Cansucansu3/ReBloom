// Formulas from SRS Equation 2.1 [cite: 177, 966, 967]
const WATER_FOOTPRINTS = {
  Cotton: 10000,
  Denim: 8000,
  Polyester: 100,
};

export const calculateSavings = (fabric, weightKg) => {
  const footprint = WATER_FOOTPRINTS[fabric] || 1000;
  return Math.round(footprint * weightKg);
};

export const getTreeStage = (score) => {
  if (score < 100) return "Seed";
  if (score < 5000) return "Sapling";
  if (score < 20000) return "Young Tree";
  if (score < 100000) return "Mature Oak";
  return "Ancient Oak";
};
