import argparse
import csv
import random
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_ZIP_PATH = ROOT_DIR / "local_datasets" / "polyvore_curated_subset.zip"
DEFAULT_DB_PATH = BACKEND_DIR / "rebloom.db"
DEFAULT_IMAGE_DIR = BACKEND_DIR / "static" / "product_images"
DEFAULT_SOURCE_PLATFORM = "polyvore-curated-subset"
DEFAULT_BASE_URL = "http://127.0.0.1:8000/static/product_images"

sys.path.insert(0, str(BACKEND_DIR))
from app.services.impact_service import (  # noqa: E402
    default_weight_for_category,
    estimate_water_saved_liters,
)


CATEGORY_ALIASES = {
    "top": "tops",
    "tops": "tops",
    "shirt": "tops",
    "shirts": "tops",
    "tshirt": "tops",
    "tshirts": "tops",
    "blouse": "tops",
    "blouses": "tops",
    "sweater": "tops",
    "sweatshirt": "tops",
    "hoodie": "tops",
    "jacket": "outerwear",
    "jackets": "outerwear",
    "coat": "outerwear",
    "outerwear": "outerwear",
    "pants": "pants",
    "trousers": "pants",
    "jeans": "pants",
    "leggings": "pants",
    "shorts": "shorts",
    "skirt": "skirts",
    "skirts": "skirts",
    "dress": "dresses",
    "dresses": "dresses",
    "one-piece": "dresses",
    "shoes": "shoes",
    "shoe": "shoes",
    "sneakers": "shoes",
    "heels": "shoes",
    "flats": "shoes",
    "boots": "shoes",
    "bag": "bags",
    "bags": "bags",
    "handbag": "bags",
    "handbags": "bags",
    "backpack": "bags",
    "clutch": "bags",
}

SELLER_NAMES = ["Cansu", "Isra", "Sena Reyyan", "Ece", "Mina", "Derya"]
BRANDS = ["Zara", "Mango", "H&M", "Pull&Bear", "Bershka", "Mavi", "Koton", "Defacto"]
CONDITIONS = ["Excellent", "Very good", "Good"]


def first_value(row, *keys, default=""):
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


def clean_text(value):
    return str(value or "").strip()


def normalize_category(row):
    fields = [
        first_value(row, "category", "rebloom_category", "source_category"),
        first_value(row, "articleType", "category_name", "item_category"),
        first_value(row, "subCategory", "subcategory"),
        first_value(row, "title", "productDisplayName", "name"),
    ]
    text = " ".join(field.lower().replace("_", " ") for field in fields if field)

    for raw, normalized in CATEGORY_ALIASES.items():
        if raw in text.split() or raw in text:
            return normalized

    return "clothing"


def normalize_gender(row):
    raw = first_value(row, "gender", "target_gender", default="Women").lower()
    text = " ".join(
        [
            raw,
            first_value(row, "title", "productDisplayName", "name").lower(),
            first_value(row, "category", "category_name").lower(),
        ]
    )

    if any(term in text for term in ["women", "woman", "female", "girl", "ladies"]):
        return "Women"
    tokens = set(text.replace("-", " ").replace("_", " ").split())
    if tokens.intersection({"men", "man", "male", "boy", "boys"}):
        return "Men"
    return "Unisex"


def infer_material(row, category):
    material = first_value(row, "material", "fabric", "fabric_composition")
    if material:
        return material

    text = " ".join(
        [
            first_value(row, "title", "productDisplayName", "name"),
            first_value(row, "articleType", "category_name", "subcategory"),
        ]
    ).lower()

    if "denim" in text or "jean" in text:
        return "Denim"
    if category in {"bags", "shoes"}:
        return "Faux leather"
    if category == "outerwear":
        return "Cotton blend"
    if category == "dresses":
        return "Cotton blend"
    return "Cotton"


def infer_size(row, category, gender):
    size = first_value(row, "size")
    if size:
        return size
    if category == "bags":
        return "One Size"
    if category == "shoes":
        return random.choice(["37", "38", "39", "40", "41"])
    if gender == "Men":
        return random.choice(["S", "M", "L", "XL"])
    return random.choice(["XS", "S", "M", "L"])


def infer_price(row, category):
    price = first_value(row, "price", "price_tl")
    if price:
        try:
            return round(float(price), 2)
        except ValueError:
            pass

    ranges = {
        "tops": (18, 55),
        "pants": (24, 75),
        "shorts": (18, 45),
        "skirts": (18, 55),
        "dresses": (30, 90),
        "outerwear": (45, 140),
        "shoes": (35, 110),
        "bags": (25, 95),
    }
    low, high = ranges.get(category, (18, 70))
    return round(random.uniform(low, high), 2)


def infer_title(row, brand, color, category):
    title = first_value(row, "title", "productDisplayName", "name", "item_name")
    if title:
        return title

    label = {
        "tops": "Top",
        "pants": "Pants",
        "shorts": "Shorts",
        "skirts": "Skirt",
        "dresses": "Dress",
        "outerwear": "Jacket",
        "shoes": "Shoes",
        "bags": "Handbag",
    }.get(category, "Fashion Item")
    return f"{brand} {color} {label}".strip()


def parse_weight(row, category):
    weight = first_value(row, "weight_kg", "weight", "estimated_weight_kg")
    if weight:
        try:
            parsed = float(weight)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return default_weight_for_category(category)


def find_csv_name(archive):
    candidates = [
        name
        for name in archive.namelist()
        if Path(name).name in {"products.csv", "styles_subset.csv", "polyvore_products.csv"}
    ]
    if candidates:
        return candidates[0]

    csv_files = [name for name in archive.namelist() if name.lower().endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError("No CSV file was found in the curated product zip.")
    return csv_files[0]


def load_rows(zip_path):
    with ZipFile(zip_path) as archive:
        csv_name = find_csv_name(archive)
        with archive.open(csv_name) as file:
            text = file.read().decode("utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def image_members_by_name(archive):
    image_suffixes = {".jpg", ".jpeg", ".png", ".webp"}
    members = {}
    for name in archive.namelist():
        suffix = Path(name).suffix.lower()
        if suffix not in image_suffixes:
            continue
        members[Path(name).name.lower()] = name
    return members


def safe_image_name(raw_name, index):
    source_name = Path(raw_name or f"polyvore_item_{index:04d}.jpg").name
    suffix = Path(source_name).suffix.lower() or ".jpg"
    stem = Path(source_name).stem.replace(" ", "_")
    known_prefixes = ("polyvore_", "deepfashion_", "curated_")
    if not stem.lower().startswith(known_prefixes):
        stem = f"curated_{stem}"
    return f"{stem}{suffix}"


def extract_image_for_row(archive, members, row, image_dir, index):
    image_file = first_value(row, "image_file", "filename", "image", "image_name", "image_path")
    if not image_file:
        return None

    member = members.get(Path(image_file).name.lower())
    if member is None:
        return None

    target_name = safe_image_name(image_file, index)
    target_path = image_dir / target_name
    image_dir.mkdir(parents=True, exist_ok=True)

    with archive.open(member) as source, target_path.open("wb") as destination:
        shutil.copyfileobj(source, destination)

    return target_name


def slugify_username(name):
    text = clean_text(name).lower()
    replacements = {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return "-".join(part for part in text.replace("_", " ").split() if part)


def get_or_create_seller(connection, seller_name):
    name = clean_text(seller_name) or "ReBloom Seller"
    row = connection.execute(
        """
        select seller_profiles.seller_id
        from seller_profiles
        join users on users.user_id = seller_profiles.user_id
        where lower(users.name) = lower(?)
        """,
        (name,),
    ).fetchone()
    if row:
        return row[0]

    username = slugify_username(name) or "rebloom-seller"
    email = f"{username}@rebloom.demo"
    user_row = connection.execute(
        "select user_id from users where lower(email) = lower(?)",
        (email,),
    ).fetchone()

    if user_row:
        user_id = user_row[0]
    else:
        cursor = connection.execute(
            """
            insert into users (name, email, password_hash, location, is_active)
            values (?, ?, ?, ?, 1)
            """,
            (name, email, "demo_import_user", "Antalya"),
        )
        user_id = cursor.lastrowid

    seller_row = connection.execute(
        "select seller_id from seller_profiles where user_id = ?",
        (user_id,),
    ).fetchone()
    if seller_row:
        return seller_row[0]

    cursor = connection.execute(
        """
        insert into seller_profiles (user_id, rating, total_sales, verified)
        values (?, 4.8, 0, 1)
        """,
        (user_id,),
    )
    return cursor.lastrowid


def get_seller_id(connection, row, index):
    seller_name = first_value(row, "seller_name", "seller", "owner")
    if not seller_name:
        seller_name = SELLER_NAMES[index % len(SELLER_NAMES)]
    return get_or_create_seller(connection, seller_name)


def existing_imported_keys(connection, source_platform):
    rows = connection.execute(
        """
        select lower(title), lower(coalesce(image_url, ''))
        from products
        where source_platform = ?
        """,
        (source_platform,),
    ).fetchall()
    return {(row[0], row[1]) for row in rows}


def deactivate_sources(connection, source_platforms):
    total = 0
    for source in source_platforms:
        cursor = connection.execute(
            "update products set is_active = 0 where source_platform = ?",
            (source,),
        )
        total += cursor.rowcount
    return total


def preview_import(zip_path):
    rows = load_rows(zip_path)
    categories = Counter(normalize_category(row) for row in rows)
    genders = Counter(normalize_gender(row) for row in rows)
    sellers = Counter(
        first_value(row, "seller_name", "seller", "owner", default="auto-assigned")
        for row in rows
    )
    return {
        "rows": len(rows),
        "categories": dict(categories.most_common()),
        "genders": dict(genders.most_common()),
        "sellers": dict(sellers.most_common(10)),
    }


def import_products(
    zip_path,
    db_path,
    image_dir,
    base_url,
    source_platform,
    replace,
    deactivate_source,
    limit,
):
    random.seed(42)
    rows = load_rows(zip_path)
    if limit:
        rows = rows[:limit]

    connection = sqlite3.connect(db_path)
    try:
        if replace:
            connection.execute(
                "update products set is_active = 0 where source_platform = ?",
                (source_platform,),
            )

        deactivated = deactivate_sources(connection, deactivate_source)
        existing_keys = set() if replace else existing_imported_keys(connection, source_platform)

        inserted = 0
        skipped = 0
        with ZipFile(zip_path) as archive:
            members = image_members_by_name(archive)

            for index, row in enumerate(rows):
                image_name = extract_image_for_row(archive, members, row, image_dir, index)
                if image_name is None:
                    skipped += 1
                    continue

                category = normalize_category(row)
                gender = normalize_gender(row)
                brand = first_value(row, "brand", "rebloom_brand", default=random.choice(BRANDS))
                color = first_value(row, "color", "baseColour", "base_color", default="Multi")
                title = infer_title(row, brand, color, category)
                material = infer_material(row, category)
                weight_kg = parse_weight(row, category)
                water_saved_liters = estimate_water_saved_liters(material, weight_kg, category)
                image_url = f"{base_url.rstrip('/')}/{image_name}"

                duplicate_key = (title.lower(), image_url.lower())
                if duplicate_key in existing_keys:
                    skipped += 1
                    continue

                seller_id = get_seller_id(connection, row, index)
                subcategory = first_value(
                    row,
                    "subcategory",
                    "subCategory",
                    "articleType",
                    "category_name",
                    default=category,
                )
                description = first_value(
                    row,
                    "description",
                    default=(
                        "Curated Polyvore-style second-hand item imported for "
                        "ReBloom visual search and outfit recommendation demos."
                    ),
                )

                connection.execute(
                    """
                    insert into products (
                        seller_id, title, description, category, subcategory, brand,
                        color, size, gender, condition, material, weight_kg,
                        water_saved_liters, price, image_url, source_platform,
                        is_second_hand, is_active
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
                    """,
                    (
                        seller_id,
                        title,
                        description,
                        category,
                        subcategory,
                        brand,
                        color,
                        infer_size(row, category, gender),
                        gender,
                        first_value(row, "condition", default=random.choice(CONDITIONS)),
                        material,
                        weight_kg,
                        water_saved_liters,
                        infer_price(row, category),
                        image_url,
                        source_platform,
                    ),
                )
                inserted += 1
                existing_keys.add(duplicate_key)

        connection.commit()
    finally:
        connection.close()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "deactivated": deactivated,
        "source_platform": source_platform,
        "images_dir": str(image_dir),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Import a curated ReBloom product subset from a zip file."
    )
    parser.add_argument("--zip", default=str(DEFAULT_ZIP_PATH))
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--source-platform", default=DEFAULT_SOURCE_PLATFORM)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "--deactivate-source",
        action="append",
        default=[],
        help="Mark products from this source_platform inactive before import. Can be repeated.",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    zip_path = Path(args.zip)
    if args.dry_run:
        print(preview_import(zip_path))
        return

    result = import_products(
        zip_path=zip_path,
        db_path=Path(args.db),
        image_dir=Path(args.image_dir),
        base_url=args.base_url,
        source_platform=args.source_platform,
        replace=args.replace,
        deactivate_source=args.deactivate_source,
        limit=args.limit,
    )
    print(result)


if __name__ == "__main__":
    main()
