from pathlib import Path

from models.clip_model import load_clip_model
from services.embedding_service import (
    get_image_embedding,
    load_embedding_index,
    load_image,
)


def cosine_similarity(left, right):
    import numpy as np

    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return float(np.dot(left, right) / (left_norm * right_norm))


def rank_by_embedding(query_embedding, embeddings, metadata, top_k=5):
    scored = []

    for index, product_embedding in enumerate(embeddings):
        scored.append(
            {
                "score": cosine_similarity(query_embedding, product_embedding),
                "product": metadata[index],
            }
        )

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def search_by_image(
    image_path,
    embeddings_path=None,
    metadata_path=None,
    top_k=5,
    model_name="ViT-B/32",
):
    kwargs = {}
    if embeddings_path:
        kwargs["embeddings_path"] = embeddings_path
    if metadata_path:
        kwargs["metadata_path"] = metadata_path

    embeddings, metadata = load_embedding_index(**kwargs)

    if len(metadata) == 0:
        return []

    model, preprocess, device = load_clip_model(model_name=model_name)
    image = load_image(Path(image_path))
    query_embedding = get_image_embedding(image, model, preprocess, device)
    return rank_by_embedding(query_embedding, embeddings, metadata, top_k=top_k)


def find_similar_products(
    product_id,
    embeddings_path=None,
    metadata_path=None,
    top_k=5,
):
    kwargs = {}
    if embeddings_path:
        kwargs["embeddings_path"] = embeddings_path
    if metadata_path:
        kwargs["metadata_path"] = metadata_path

    embeddings, metadata = load_embedding_index(**kwargs)
    query_index = None

    for index, product in enumerate(metadata):
        if str(product.get("product_id") or product.get("id")) == str(product_id):
            query_index = index
            break

    if query_index is None:
        return []

    results = rank_by_embedding(embeddings[query_index], embeddings, metadata, top_k=top_k + 1)
    return [
        result for result in results
        if str(result["product"].get("product_id") or result["product"].get("id")) != str(product_id)
    ][:top_k]
