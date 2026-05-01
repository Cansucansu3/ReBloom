import argparse
import csv
import hashlib
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS_PATH = BASE_DIR / "data" / "products.csv"
DEFAULT_OUTPUT_PATH = BASE_DIR / "embeddings" / "products_embeddings.json"


def product_to_text(product):
    fields = [
        product.get("title"),
        product.get("category"),
        product.get("subcategory"),
        product.get("brand"),
        product.get("color"),
        product.get("material"),
        product.get("description"),
    ]
    return " ".join(str(field or "") for field in fields)


def text_to_embedding(text, dimensions=32):
    digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
    values = []

    while len(values) < dimensions:
        for byte in digest:
            values.append((byte / 255.0) * 2.0 - 1.0)
            if len(values) == dimensions:
                break
        digest = hashlib.sha256(digest).digest()

    return values


def load_products(path=DEFAULT_PRODUCTS_PATH):
    with Path(path).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_embeddings(products):
    records = []

    for product in products:
        text = product_to_text(product)
        records.append(
            {
                "product_id": product["product_id"],
                "title": product["title"],
                "embedding": text_to_embedding(text),
                "metadata": product,
            }
        )

    return records


def save_embeddings(records, output_path=DEFAULT_OUTPUT_PATH):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Build demo product embeddings.")
    parser.add_argument("--products", default=DEFAULT_PRODUCTS_PATH)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    products = load_products(args.products)
    records = build_embeddings(products)
    save_embeddings(records, args.output)
    print(f"Saved {len(records)} embeddings to {args.output}")


if __name__ == "__main__":
    main()
