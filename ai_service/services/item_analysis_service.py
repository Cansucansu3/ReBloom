from functools import lru_cache

import numpy as np

from services.compatibility_service import (
    get_clip_embedding,
    load_clip_artifact,
    load_image_from_value,
)


CATEGORY_PROMPTS = {
    "tops": ["a clothing product photo of a shirt", "a t-shirt", "a blouse", "a top"],
    "pants": ["a clothing product photo of jeans", "long pants", "trousers"],
    "shorts": ["a pair of shorts", "short pants"],
    "skirts": ["a skirt", "a denim skirt", "a mini skirt"],
    "dresses": ["a dress", "a one piece dress"],
    "shoes": ["a pair of shoes", "sneakers", "sandals", "heels"],
    "bags": ["a handbag", "a backpack", "a fashion bag"],
    "outerwear": ["a jacket", "a sweatshirt", "a sweater", "a coat"],
}

FASHION_PROMPTS = {
    "fashion_item": [
        "a product photo of clothing",
        "a fashion item on a plain background",
        "a shoe or handbag product photo",
    ],
    "not_fashion": [
        "food",
        "furniture",
        "a landscape",
        "a face",
        "a cosmetic product",
        "a random object that is not clothing",
    ],
}

PATTERN_PROMPTS = {
    "Solid": ["solid color fabric", "plain clothing with no pattern"],
    "Striped": ["striped fabric", "clothing with stripes"],
    "Checked": ["checked fabric", "plaid fabric"],
    "Floral": ["floral print fabric", "flower patterned clothing"],
    "Graphic print": ["graphic print t-shirt", "printed clothing"],
    "Denim": ["denim fabric", "blue jean fabric"],
}

CATEGORY_DEFAULTS = {
    "tops": {"material": "Cotton", "weight_kg": 0.30},
    "pants": {"material": "Cotton blend", "weight_kg": 0.60},
    "shorts": {"material": "Cotton blend", "weight_kg": 0.35},
    "skirts": {"material": "Cotton", "weight_kg": 0.40},
    "dresses": {"material": "Cotton", "weight_kg": 0.50},
    "shoes": {"material": "Synthetic", "weight_kg": 0.80},
    "bags": {"material": "Canvas", "weight_kg": 0.50},
    "outerwear": {"material": "Cotton blend", "weight_kg": 0.80},
}

COLOR_PALETTE = {
    "Black": (25, 25, 25),
    "White": (240, 240, 235),
    "Grey": (135, 135, 135),
    "Blue": (55, 105, 175),
    "Navy Blue": (25, 45, 85),
    "Brown": (105, 70, 45),
    "Beige": (205, 185, 150),
    "Green": (65, 130, 70),
    "Pink": (220, 120, 165),
    "Red": (185, 45, 45),
    "Purple": (115, 75, 155),
    "Yellow": (220, 190, 70),
    "Orange": (215, 120, 45),
}


def softmax(scores, temperature=30):
    values = np.array(scores, dtype=np.float32) * temperature
    values = values - np.max(values)
    exp_values = np.exp(values)
    return exp_values / np.sum(exp_values)


@lru_cache(maxsize=32)
def get_prompt_embeddings(cache_key):
    import clip
    import torch

    prompt_groups = {
        "category": CATEGORY_PROMPTS,
        "fashion": FASHION_PROMPTS,
        "pattern": PATTERN_PROMPTS,
    }[cache_key]

    model, _, device = load_clip_artifact()
    labels = []
    embeddings = []

    for label, prompts in prompt_groups.items():
        tokens = clip.tokenize(prompts).to(device)
        with torch.no_grad():
            text_features = model.encode_text(tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        embedding = text_features.mean(dim=0, keepdim=True)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        labels.append(label)
        embeddings.append(embedding.cpu().numpy()[0])

    return labels, np.array(embeddings)


def classify_embedding(image_embedding, cache_key):
    labels, embeddings = get_prompt_embeddings(cache_key)
    scores = embeddings @ image_embedding
    probabilities = softmax(scores)
    best_index = int(np.argmax(probabilities))
    ranked = sorted(
        (
            {
                "label": labels[index],
                "score": float(scores[index]),
                "confidence": float(probabilities[index]),
            }
            for index in range(len(labels))
        ),
        key=lambda item: item["confidence"],
        reverse=True,
    )
    return ranked[0], ranked


def dominant_color_name(image):
    rgb_image = image.convert("RGB").resize((96, 96))
    pixels = np.asarray(rgb_image).reshape(-1, 3).astype(np.float32)

    brightness = pixels.mean(axis=1)
    channel_spread = pixels.max(axis=1) - pixels.min(axis=1)
    non_background = ~((brightness > 235) & (channel_spread < 20))
    usable_pixels = pixels[non_background]
    if len(usable_pixels) < 50:
        usable_pixels = pixels

    color_std = usable_pixels.std(axis=0).mean()
    mean_color = usable_pixels.mean(axis=0)
    if color_std > 70:
        return "Multi"

    best_color = min(
        COLOR_PALETTE.items(),
        key=lambda item: float(np.sum((mean_color - np.array(item[1])) ** 2)),
    )
    return best_color[0]


def material_for_prediction(category, pattern, color):
    if pattern == "Denim" or (
        category in {"pants", "shorts", "skirts"} and color in {"Blue", "Navy Blue"}
    ):
        return "Denim"

    return CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["tops"])["material"]


def title_hint(category, color, pattern):
    category_label = {
        "tops": "Top",
        "pants": "Pants",
        "shorts": "Shorts",
        "skirts": "Skirt",
        "dresses": "Dress",
        "shoes": "Shoes",
        "bags": "Bag",
        "outerwear": "Jacket",
    }.get(category, "Item")

    if pattern and pattern not in {"Solid"}:
        return f"{color} {pattern} {category_label}".strip()
    return f"{color} {category_label}".strip()


def analyze_item_image(query_image_value):
    image = load_image_from_value(query_image_value)
    if image is None:
        return {"is_fashion": False, "error": "Image could not be loaded"}

    try:
        image_embedding = get_clip_embedding(image.convert("RGB"))
    except Exception:
        return {"is_fashion": False, "error": "Image could not be analyzed"}

    fashion_best, fashion_scores = classify_embedding(image_embedding, "fashion")
    category_best, category_scores = classify_embedding(image_embedding, "category")
    pattern_best, pattern_scores = classify_embedding(image_embedding, "pattern")

    category = category_best["label"]
    color = dominant_color_name(image)
    pattern = pattern_best["label"]
    material = material_for_prediction(category, pattern, color)
    weight = CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["tops"])["weight_kg"]
    fashion_score = next(
        item["confidence"]
        for item in fashion_scores
        if item["label"] == "fashion_item"
    )
    is_fashion = fashion_score >= 0.55

    return {
        "is_fashion": is_fashion,
        "fashion_confidence": round(float(fashion_score), 3),
        "category": category,
        "category_confidence": round(float(category_best["confidence"]), 3),
        "category_scores": {
            item["label"]: round(float(item["confidence"]), 3)
            for item in category_scores[:4]
        },
        "color": color,
        "pattern": pattern,
        "pattern_confidence": round(float(pattern_best["confidence"]), 3),
        "material": material,
        "weight_kg": weight,
        "title_hint": title_hint(category, color, pattern),
        "rejected_reason": None if is_fashion else "Image does not look like a fashion item",
    }
