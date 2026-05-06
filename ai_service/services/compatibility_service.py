import base64
import io
import urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from models.clip_model import load_clip_model


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "polyvore_compatibility_model.joblib"


def image_from_bytes(content):
    return Image.open(io.BytesIO(content)).convert("RGB")


def image_from_data_url(data_url):
    _, encoded = data_url.split(",", 1)
    return image_from_bytes(base64.b64decode(encoded))


def image_from_url(url):
    with urllib.request.urlopen(url, timeout=8) as response:
        return image_from_bytes(response.read())


def load_image_from_value(value):
    if not value:
        return None

    try:
        if value.startswith("data:image"):
            return image_from_data_url(value)
        if value.startswith("http://") or value.startswith("https://"):
            return image_from_url(value)
        path = Path(value)
        if path.exists():
            return Image.open(path).convert("RGB")
    except Exception:
        return None

    return None


@lru_cache(maxsize=1)
def load_compatibility_artifact(model_path=str(DEFAULT_MODEL_PATH)):
    import joblib

    artifact = joblib.load(model_path)
    model = artifact["model"] if isinstance(artifact, dict) else artifact
    if hasattr(model, "n_jobs"):
        model.n_jobs = 1
    return artifact, model


@lru_cache(maxsize=1)
def load_clip_artifact():
    return load_clip_model()


def get_clip_embedding(image):
    import torch

    model, preprocess, device = load_clip_artifact()
    image_input = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        features = model.encode_image(image_input)
        features = features / features.norm(dim=-1, keepdim=True)

    return features.cpu().numpy().flatten()


def build_pair_features(left_embedding, right_embedding):
    return np.concatenate(
        [
            left_embedding,
            right_embedding,
            np.abs(left_embedding - right_embedding),
            left_embedding * right_embedding,
        ]
    ).reshape(1, -1)


def compatibility_score(left_image, right_image, model_path=str(DEFAULT_MODEL_PATH)):
    _, model = load_compatibility_artifact(model_path)
    left_embedding = get_clip_embedding(left_image)
    right_embedding = get_clip_embedding(right_image)
    features = build_pair_features(left_embedding, right_embedding)

    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        probabilities = model.predict_proba(features)[0]
        if 1 in classes:
            return float(probabilities[classes.index(1)])

    return float(model.predict(features)[0])


def rank_outfit_candidates(base_product, candidates, limit=6):
    base_image = load_image_from_value(base_product.get("image_url"))
    if base_image is None:
        return []

    ranked = []
    for candidate in candidates:
        candidate_image = load_image_from_value(candidate.get("image_url"))
        if candidate_image is None:
            continue

        try:
            score = compatibility_score(base_image, candidate_image)
        except Exception:
            continue

        ranked.append(
            {
                "product_id": candidate.get("product_id"),
                "score": score,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]
