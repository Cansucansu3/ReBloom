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

export const VIRTUAL_TREE_GOAL_LITERS = 10000;
export const LEGACY_GOAL_LITERS = 100000;
export const REAL_TREE_GOAL_LITERS = LEGACY_GOAL_LITERS;
export const GARDEN_PLOTS_PER_LEVEL = 12;

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

export const TREE_STAGES = [
  {
    key: "seed",
    label: "Seed",
    min: 0,
    next: 1000,
    description: "Your garden has started.",
  },
  {
    key: "sapling",
    label: "Sapling",
    min: 1000,
    next: 4000,
    description: "Your first leaves are growing.",
  },
  {
    key: "young_tree",
    label: "Young Tree",
    min: 4000,
    next: 7000,
    description: "Your impact is becoming visible.",
  },
  {
    key: "mature_oak",
    label: "Mature Oak",
    min: 7000,
    next: VIRTUAL_TREE_GOAL_LITERS,
    description: "Your garden is getting stronger.",
  },
  {
    key: "ancient_oak",
    label: "Ancient Oak",
    min: VIRTUAL_TREE_GOAL_LITERS,
    next: null,
    description: "You reached the legacy tree stage.",
  },
];

export const getTreeImageFilename = (stageKey, options = {}) => {
  if (options.animated && stageKey === "mature_oak") {
    return "mature_tree_animated.gif";
  }

  return `${stageKey}.png`;
};

export const getTreeStageInfo = (score) => {
  const value = Number(score) || 0;
  if (value < 1000) return TREE_STAGES[0];
  if (value < 4000) return TREE_STAGES[1];
  if (value < 7000) return TREE_STAGES[2];
  if (value < VIRTUAL_TREE_GOAL_LITERS) return TREE_STAGES[3];
  return TREE_STAGES[4];
};

export const getTreeStage = (score) => {
  return getTreeStageInfo(score).label;
};

export const getCurrentTreeLiters = (totalWaterSaved) => {
  const total = Math.max(0, Number(totalWaterSaved || 0));
  return total % VIRTUAL_TREE_GOAL_LITERS;
};

export const getCompletedVirtualTrees = (totalWaterSaved) => {
  const total = Math.max(0, Number(totalWaterSaved || 0));
  return Math.floor(total / VIRTUAL_TREE_GOAL_LITERS);
};

export const getRealTreesEarned = (totalWaterSaved) => {
  const total = Math.max(0, Number(totalWaterSaved || 0));
  return Math.floor(total / REAL_TREE_GOAL_LITERS);
};

export const getCurrentTreeProgressPercent = (currentTreeLiters) => {
  const current = Math.max(0, Number(currentTreeLiters || 0));
  return Math.max(3, Math.min((current / VIRTUAL_TREE_GOAL_LITERS) * 100, 100));
};

export const getGardenLevelInfo = (completedTrees, slotCount = GARDEN_PLOTS_PER_LEVEL) => {
  const completed = Math.max(0, Number(completedTrees || 0));
  const level = Math.floor(completed / slotCount) + 1;
  const completedBeforeLevel = (level - 1) * slotCount;
  const completedInLevel = completed - completedBeforeLevel;

  return {
    level,
    completedBeforeLevel,
    completedInLevel,
    slotCount,
  };
};

export const buildGardenSlots = (completedTrees, currentStageKey, slotCount = GARDEN_PLOTS_PER_LEVEL) => {
  const levelInfo = getGardenLevelInfo(completedTrees, slotCount);
  const completedInLevel = levelInfo.completedInLevel;
  const hasCurrentTreeSlot = completedInLevel < slotCount;

  return Array.from({ length: slotCount }, (_, index) => {
    if (index < completedInLevel) {
      return {
        id: index,
        filled: true,
        stage: "mature_oak",
      };
    }

    if (hasCurrentTreeSlot && index === completedInLevel) {
      return {
        id: index,
        filled: true,
        inProgress: true,
        stage: currentStageKey,
      };
    }

    return {
      id: index,
      filled: false,
      stage: null,
    };
  });
};
