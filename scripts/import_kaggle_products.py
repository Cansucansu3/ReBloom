import argparse
import csv
import random
import shutil
import sqlite3
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ZIP_PATH = ROOT_DIR / "local_datasets" / "rebloom_fashion_subset.zip"
DEFAULT_DB_PATH = ROOT_DIR / "backend" / "rebloom.db"
DEFAULT_IMAGE_DIR = ROOT_DIR / "backend" / "static" / "product_images"
DEFAULT_SOURCE_PLATFORM = "kaggle-fashion-subset"


def normalize_category(row):
    subcategory = (row.get("subCategory") or "").strip().lower()
    article_type = (row.get("articleType") or "").strip().lower()
    master_category = (row.get("masterCategory") or "").strip().lower()

    text = f"{subcategory} {article_type}"
    if any(term in text for term in ["shirt", "tshirt", "top", "kurti", "tunic", "sweater", "sweatshirt", "jacket"]):
        return "tops"
    if any(term in text for term in ["jeans", "pants", "trouser", "track pants", "shorts", "churidar"]):
        return "pants"
    if "skirt" in text:
        return "skirts"
    if "dress" in text:
        return "dresses"
    if any(term in text for term in ["shoe", "heel", "flat", "sandal", "flip flop"]):
        return "shoes"
    if any(term in text for term in ["bag", "handbag", "backpack"]):
        return "bags"
    if master_category == "footwear":
        return "shoes"
    if master_category == "accessories":
        return "bags"
    return "clothing"


def infer_size(row):
    category = normalize_category(row)
    gender = (row.get("gender") or "").lower()
    if category == "shoes":
        return random.choice(["37", "38", "39", "40", "41", "42", "43"])
    if category == "bags":
        return "One Size"
    if "men" in gender:
        return random.choice(["S", "M", "L", "XL"])
    return random.choice(["XS", "S", "M", "L"])


def infer_material(row):
    article_type = (row.get("articleType") or "").lower()
    product_name = (row.get("productDisplayName") or "").lower()
    text = f"{article_type} {product_name}"
    if "jeans" in text:
        return "Denim"
    if any(term in text for term in ["shoe", "heel", "flat", "sandal"]):
        return "Synthetic"
    if "bag" in text:
        return "Faux leather"
    if any(term in text for term in ["sweater", "sweatshirt"]):
        return "Cotton blend"
    return "Cotton"


def price_for_category(category):
    ranges = {
        "tops": (14, 45),
        "pants": (18, 55),
        "skirts": (16, 48),
        "dresses": (24, 70),
        "shoes": (25, 85),
        "bags": (18, 65),
    }
    low, high = ranges.get(category, (12, 60))
    return round(random.uniform(low, high), 2)


def load_subset(zip_path):
    with ZipFile(zip_path) as archive:
        csv_name = next(
            (name for name in archive.namelist() if name.endswith("styles_subset.csv")),
            None,
        )
        if csv_name is None:
            raise FileNotFoundError("styles_subset.csv was not found in the zip file.")

        with archive.open(csv_name) as file:
            text = file.read().decode("utf-8")

    return list(csv.DictReader(text.splitlines()))


def extract_images(zip_path, image_dir):
    image_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.startswith("images/") or Path(name).suffix.lower() not in {
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            }:
                continue

            target = image_dir / Path(name).name
            with archive.open(name) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)


def get_seller_ids(connection):
    rows = connection.execute(
        "select seller_id from seller_profiles order by seller_id"
    ).fetchall()
    seller_ids = [row[0] for row in rows]
    if not seller_ids:
        raise RuntimeError("No seller_profiles found. Create at least one seller first.")
    return seller_ids


def existing_imported_names(connection, source_platform):
    rows = connection.execute(
        "select title from products where source_platform = ?",
        (source_platform,),
    ).fetchall()
    return {row[0] for row in rows}


def import_products(zip_path, db_path, image_dir, base_url, replace, source_platform):
    random.seed(42)
    rows = load_subset(zip_path)
    extract_images(zip_path, image_dir)

    connection = sqlite3.connect(db_path)
    try:
        seller_ids = get_seller_ids(connection)

        if replace:
            connection.execute(
                "delete from products where source_platform = ?",
                (source_platform,),
            )
            existing_names = set()
        else:
            existing_names = existing_imported_names(connection, source_platform)

        inserted = 0
        skipped = 0

        for index, row in enumerate(rows):
            title = (row.get("productDisplayName") or "").strip()
            image_file = (row.get("image_file") or "").strip()
            if not title or not image_file:
                skipped += 1
                continue

            if title in existing_names:
                skipped += 1
                continue

            image_path = image_dir / image_file
            if not image_path.exists():
                skipped += 1
                continue

            category = normalize_category(row)
            seller_id = seller_ids[index % len(seller_ids)]
            article_type = (row.get("articleType") or "").strip()
            usage = (row.get("usage") or "Casual").strip()
            gender = (row.get("gender") or "Unisex").strip()
            brand = (row.get("rebloom_brand") or "ReBloom Finds").strip()
            color = (row.get("baseColour") or "Multi").strip()
            description = (
                f"{gender} {usage.lower()} {article_type.lower()} from the Kaggle fashion subset. "
                "Imported for ReBloom visual search testing."
            )
            image_url = f"{base_url.rstrip('/')}/{image_file}"

            connection.execute(
                """
                insert into products (
                    seller_id, title, description, category, subcategory, brand, color,
                    size, condition, material, price, image_url, source_platform,
                    is_second_hand, is_active
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seller_id,
                    title,
                    description,
                    category,
                    article_type,
                    brand,
                    color,
                    infer_size(row),
                    random.choice(["Excellent", "Good", "Very good"]),
                    infer_material(row),
                    price_for_category(category),
                    image_url,
                    source_platform,
                    1,
                    1,
                ),
            )
            inserted += 1

        connection.commit()
    finally:
        connection.close()

    return {"inserted": inserted, "skipped": skipped, "images_dir": str(image_dir)}


def preview_import(zip_path):
    rows = load_subset(zip_path)
    categories = Counter(normalize_category(row) for row in rows)
    article_types = Counter((row.get("articleType") or "Unknown").strip() for row in rows)
    brands = Counter((row.get("rebloom_brand") or "Unknown").strip() for row in rows)

    return {
        "rows": len(rows),
        "categories": dict(categories.most_common()),
        "top_article_types": dict(article_types.most_common(12)),
        "brands": dict(brands.most_common()),
    }


def main():
    parser = argparse.ArgumentParser(description="Import ReBloom Kaggle fashion subset.")
    parser.add_argument("--zip", default=str(DEFAULT_ZIP_PATH))
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/static/product_images",
    )
    parser.add_argument("--source-platform", default=DEFAULT_SOURCE_PLATFORM)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete previously imported Kaggle subset products before importing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the subset without writing images or database rows.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print(preview_import(Path(args.zip)))
        return

    result = import_products(
        zip_path=Path(args.zip),
        db_path=Path(args.db),
        image_dir=Path(args.image_dir),
        base_url=args.base_url,
        replace=args.replace,
        source_platform=args.source_platform,
    )
    print(result)


if __name__ == "__main__":
    main()
