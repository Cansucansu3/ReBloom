import csv
import json
from pathlib import Path

from models.clip_model import load_clip_model


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS_PATH = BASE_DIR / "data" / "products.csv"
DEFAULT_EMBEDDINGS_PATH = BASE_DIR / "data" / "product_embeddings.npy"
DEFAULT_METADATA_PATH = BASE_DIR / "data" / "product_metadata.json"


def load_products(products_path=DEFAULT_PRODUCTS_PATH):
    with Path(products_path).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_image(image_path):
    from PIL import Image

    return Image.open(image_path).convert("RGB")


def get_image_embedding(image, model, preprocess, device):
    import torch

    image_input = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image_input)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    return image_features.cpu().numpy().flatten()


def resolve_image_path(product, products_path=DEFAULT_PRODUCTS_PATH):
    image_path = product.get("image_path") or product.get("filename")
    if not image_path:
        return None

    path = Path(image_path)
    if path.is_absolute():
        return path

    return Path(products_path).resolve().parents[1] / path


def build_product_embeddings(
    products_path=DEFAULT_PRODUCTS_PATH,
    embeddings_path=DEFAULT_EMBEDDINGS_PATH,
    metadata_path=DEFAULT_METADATA_PATH,
    model_name="ViT-B/32",
):
    import numpy as np

    products = load_products(products_path)
    model, preprocess, device = load_clip_model(model_name=model_name)
    embeddings = []
    metadata = []
    skipped = []

    for product in products:
        image_path = resolve_image_path(product, products_path)

        if image_path is None or not image_path.exists():
            skipped.append(product.get("title") or product.get("product_id"))
            continue

        image = load_image(image_path)
        embedding = get_image_embedding(image, model, preprocess, device)
        embeddings.append(embedding)
        metadata.append(product)

    embeddings_path = Path(embeddings_path)
    metadata_path = Path(metadata_path)
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    if embeddings:
        np.save(embeddings_path, np.vstack(embeddings))
    else:
        np.save(embeddings_path, np.empty((0, 0)))

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    return {
        "count": len(metadata),
        "skipped": skipped,
        "embeddings_path": str(embeddings_path),
        "metadata_path": str(metadata_path),
    }


def load_embedding_index(
    embeddings_path=DEFAULT_EMBEDDINGS_PATH,
    metadata_path=DEFAULT_METADATA_PATH,
):
    import numpy as np

    embeddings = np.load(embeddings_path)

    with Path(metadata_path).open(encoding="utf-8") as file:
        metadata = json.load(file)

    return embeddings, metadata
