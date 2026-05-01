import base64
import io
import urllib.request

import numpy as np
from PIL import Image


def image_from_bytes(content):
    return Image.open(io.BytesIO(content)).convert("RGB")


def image_from_data_url(data_url):
    _, encoded = data_url.split(",", 1)
    return image_from_bytes(base64.b64decode(encoded))


def image_from_url(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return image_from_bytes(response.read())


def load_product_image(image_url):
    if not image_url:
        return None

    try:
        if image_url.startswith("data:image"):
            return image_from_data_url(image_url)
        if image_url.startswith("http://") or image_url.startswith("https://"):
            return image_from_url(image_url)
    except Exception:
        return None

    return None


def get_image_embedding(image):
    image = image.resize((64, 64))
    array = np.asarray(image, dtype=np.float32) / 255.0
    channels = [array[:, :, index] for index in range(3)]
    features = []

    for channel in channels:
        histogram, _ = np.histogram(channel, bins=8, range=(0.0, 1.0))
        features.extend(histogram.astype(np.float32).tolist())

    features.extend(array.mean(axis=(0, 1)).tolist())
    features.extend(array.std(axis=(0, 1)).tolist())
    embedding = np.asarray(features, dtype=np.float32)
    norm = np.linalg.norm(embedding)

    if norm == 0:
        return embedding

    return embedding / norm


def cosine_similarity(left, right):
    return float(np.dot(left, right))


def find_visually_similar_products(query_image, products, limit=12):
    query_embedding = get_image_embedding(query_image)
    results = []

    for product in products:
        product_image = load_product_image(product.image_url)
        if product_image is None:
            continue

        product_embedding = get_image_embedding(product_image)
        results.append((cosine_similarity(query_embedding, product_embedding), product))

    results.sort(key=lambda item: item[0], reverse=True)
    return results[:limit]
