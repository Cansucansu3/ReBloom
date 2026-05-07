const WATER_FOOTPRINTS = {
  cotton: 10000,
  denim: 8000,
  polyester: 100,
  "recycled polyester": 60,
  synthetic: 500,
  "faux leather": 900,
  canvas: 4000,
  "cotton blend": 5000,
};

const normalizeMaterial = (value) => {
  const text = String(value || "").trim().toLowerCase();

  if (text.includes("recycled") && text.includes("polyester")) {
    return "recycled polyester";
  }
  if (text.includes("faux") && text.includes("leather")) {
    return "faux leather";
  }
  if (text.includes("cotton") && text.includes("blend")) {
    return "cotton blend";
  }

  return Object.keys(WATER_FOOTPRINTS).find((material) => text.includes(material)) || text;
};

const parseComposition = (fabric) => {
  const text = String(fabric || "").trim();
  const matches = [...text.matchAll(/(\d+(?:\.\d+)?)\s*%\s*([A-Za-z ]+)/g)];

  if (!matches.length) {
    return [[normalizeMaterial(text) || "cotton blend", 1]];
  }

  const parts = matches.map((match) => [
    normalizeMaterial(match[2]),
    Number(match[1]) / 100,
  ]);
  const total = parts.reduce((sum, [, share]) => sum + share, 0) || 1;

  return parts.map(([material, share]) => [material, share / total]);
};

export const calculateSavings = (fabric, weightKg) => {
  const numericWeight = Number(weightKg);
  const weight = Number.isFinite(numericWeight) && numericWeight > 0 ? numericWeight : 0.5;
  const footprint = parseComposition(fabric).reduce(
    (sum, [material, share]) => sum + (WATER_FOOTPRINTS[material] || 1000) * share,
    0
  );

  return Math.round(footprint * weight);
};

export const getTreeStage = (score) => {
  if (score < 100) return "Seed";
  if (score < 5000) return "Sapling";
  if (score < 20000) return "Young Tree";
  if (score < 100000) return "Mature Oak";
  return "Ancient Oak";
};
