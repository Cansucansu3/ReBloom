"""
Train a ReBloom Polyvore outfit compatibility classifier.

This script is meant for Kaggle/Colab experiments. It builds cleaner pairwise
training data from Polyvore outfits by:

1. using compatible outfits for positive pairs,
2. generating category-controlled negative pairs from different outfits,
3. splitting by outfit id before pair generation to reduce leakage,
4. comparing several classifiers on the same visual embeddings.

The default feature extractor is CLIP ViT-B/32, which is compatible with the
current ReBloom AI service. DINOv2 is also supported for comparison experiments,
but a DINOv2-trained artifact requires service-side DINOv2 embedding support
before it can replace the production CLIP-based model.

Example:
    python train_polyvore_compatibility_model.py \
        --dataset-dir /content/polyvore-outfits \
        --output-dir /content/rebloom_polyvore_clip \
        --data-format hf_parquet \
        --polyvore-split disjoint \
        --max-positive-outfits 10000 \
        --feature-extractor clip

DINOv2 comparison example:
    pip install transformers
    python train_polyvore_compatibility_model.py \
        --dataset-dir /content/polyvore-outfits \
        --output-dir /content/rebloom_polyvore_dinov2 \
        --data-format hf_parquet \
        --polyvore-split disjoint \
        --max-positive-outfits 10000 \
        --feature-extractor dinov2
"""

from __future__ import annotations

import argparse
import csv
import io
import itertools
import json
import random
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from PIL import Image, ImageFile
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


ImageFile.LOAD_TRUNCATED_IMAGES = True

TARGET_CATEGORIES = [
    "tops",
    "pants",
    "shorts",
    "skirts",
    "dresses",
    "outerwear",
    "shoes",
    "bags",
]

COMPLEMENTARY_CATEGORIES = {
    "tops": {"pants", "shorts", "skirts", "shoes", "bags", "outerwear"},
    "pants": {"tops", "shoes", "bags", "outerwear"},
    "shorts": {"tops", "shoes", "bags", "outerwear"},
    "skirts": {"tops", "shoes", "bags", "outerwear"},
    "dresses": {"shoes", "bags", "outerwear"},
    "outerwear": {"tops", "pants", "shorts", "skirts", "dresses", "shoes"},
    "shoes": {"tops", "pants", "shorts", "skirts", "dresses", "bags"},
    "bags": {"tops", "pants", "shorts", "skirts", "dresses", "shoes"},
}

CATEGORY_ALIASES = {
    "top": "tops",
    "tops": "tops",
    "shirt": "tops",
    "shirts": "tops",
    "tshirt": "tops",
    "tshirts": "tops",
    "t-shirt": "tops",
    "t-shirts": "tops",
    "tee": "tops",
    "blouse": "tops",
    "blouses": "tops",
    "sweater": "outerwear",
    "sweaters": "outerwear",
    "sweatshirt": "outerwear",
    "sweatshirts": "outerwear",
    "jacket": "outerwear",
    "jackets": "outerwear",
    "coat": "outerwear",
    "coats": "outerwear",
    "outerwear": "outerwear",
    "outwear": "outerwear",
    "bottom": "pants",
    "bottoms": "pants",
    "pant": "pants",
    "pants": "pants",
    "trouser": "pants",
    "trousers": "pants",
    "jean": "pants",
    "jeans": "pants",
    "legging": "pants",
    "leggings": "pants",
    "short": "shorts",
    "shorts": "shorts",
    "skirt": "skirts",
    "skirts": "skirts",
    "dress": "dresses",
    "dresses": "dresses",
    "romper": "dresses",
    "jumpsuit": "dresses",
    "shoe": "shoes",
    "shoes": "shoes",
    "sneaker": "shoes",
    "sneakers": "shoes",
    "heel": "shoes",
    "heels": "shoes",
    "sandal": "shoes",
    "sandals": "shoes",
    "boot": "shoes",
    "boots": "shoes",
    "flat": "shoes",
    "flats": "shoes",
    "bag": "bags",
    "bags": "bags",
    "handbag": "bags",
    "handbags": "bags",
    "purse": "bags",
    "purses": "bags",
    "backpack": "bags",
    "backpacks": "bags",
    "clutch": "bags",
    "clutches": "bags",
}

TEXT_CATEGORY_HINTS = [
    (("t-shirt", "tshirt", "shirt", "blouse", "top", "tee", "camisole"), "tops"),
    (("sweater", "sweatshirt", "jacket", "coat", "blazer", "hoodie"), "outerwear"),
    (("shorts",), "shorts"),
    (("skirt",), "skirts"),
    (("dress", "romper", "jumpsuit"), "dresses"),
    (("jean", "pants", "trouser", "legging"), "pants"),
    (("shoe", "sneaker", "heel", "sandal", "boot", "flat"), "shoes"),
    (("bag", "handbag", "purse", "backpack", "clutch"), "bags"),
]

COMMON_METADATA_NAMES = [
    "polyvore_item_metadata.json",
    "item_metadata.json",
    "metadata.json",
    "items.json",
]

COMMON_COMPATIBILITY_NAMES = [
    "compatibility_train.txt",
    "compatibility_valid.txt",
    "compatibility_val.txt",
    "compatibility_test.txt",
    "train_compatibility.txt",
    "valid_compatibility.txt",
    "test_compatibility.txt",
    "train.txt",
    "valid.txt",
    "test.txt",
]


@dataclass(frozen=True)
class Outfit:
    outfit_id: str
    item_ids: tuple[str, ...]
    label: int
    source_split: str


@dataclass(frozen=True)
class ItemRecord:
    item_id: str
    outfit_id: str
    category: str
    image_path: str


@dataclass(frozen=True)
class PairRecord:
    left_item_id: str
    right_item_id: str
    left_image_path: str
    right_image_path: str
    left_category: str
    right_category: str
    label: int
    split: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--data-format",
        choices=["auto", "files", "hf_parquet"],
        default="auto",
        help="Use hf_parquet for mvasil/polyvore-outfits from Hugging Face.",
    )
    parser.add_argument(
        "--polyvore-split",
        choices=["disjoint", "nondisjoint"],
        default="disjoint",
        help="Polyvore split variant used by Hugging Face dataset files.",
    )
    parser.add_argument("--metadata-file", type=Path, default=None)
    parser.add_argument("--image-dir", type=Path, default=None)
    parser.add_argument(
        "--compatibility-files",
        type=Path,
        nargs="*",
        default=None,
        help="Optional compatibility txt/json files. Auto-detected if omitted.",
    )
    parser.add_argument("--max-positive-outfits", type=int, default=10000)
    parser.add_argument("--max-pairs-per-outfit", type=int, default=10)
    parser.add_argument("--negative-ratio", type=float, default=1.0)
    parser.add_argument("--max-pairs", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--feature-extractor",
        choices=["clip", "dinov2"],
        default="clip",
    )
    parser.add_argument("--clip-model", default="ViT-B/32")
    parser.add_argument("--hf-model", default="facebook/dinov2-base")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["logreg", "linear_svm", "random_forest", "mlp"],
        choices=["logreg", "linear_svm", "random_forest", "mlp"],
    )
    parser.add_argument("--random-forest-estimators", type=int, default=200)
    parser.add_argument("--mlp-max-iter", type=int, default=250)
    parser.add_argument(
        "--selection-metric",
        choices=["validation_macro_f1", "validation_compatible_f1", "validation_roc_auc"],
        default="validation_macro_f1",
    )
    parser.add_argument(
        "--refit-train-val",
        action="store_true",
        help="Refit the selected algorithm on train+validation before saving.",
    )
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_first_existing(dataset_dir: Path, names: list[str]) -> Path | None:
    for name in names:
        direct = dataset_dir / name
        if direct.exists():
            return direct

    for name in names:
        matches = list(dataset_dir.rglob(name))
        if matches:
            return matches[0]

    return None


def find_metadata_file(dataset_dir: Path, provided: Path | None) -> Path:
    if provided:
        if not provided.exists():
            raise FileNotFoundError(f"Metadata file not found: {provided}")
        return provided

    found = find_first_existing(dataset_dir, COMMON_METADATA_NAMES)
    if not found:
        raise FileNotFoundError(
            "Could not auto-detect Polyvore metadata. Pass --metadata-file."
        )
    return found


def find_image_dir(dataset_dir: Path, provided: Path | None) -> Path:
    if provided:
        if not provided.exists():
            raise FileNotFoundError(f"Image directory not found: {provided}")
        return provided

    candidates = [
        dataset_dir / "images",
        dataset_dir / "image",
        dataset_dir / "polyvore_images",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    image_dirs = [
        path
        for path in dataset_dir.rglob("*")
        if path.is_dir() and path.name.lower() in {"images", "image"}
    ]
    if image_dirs:
        return image_dirs[0]

    return dataset_dir


def find_compatibility_files(
    dataset_dir: Path,
    provided: list[Path] | None,
) -> list[Path]:
    if provided:
        missing = [path for path in provided if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Compatibility files not found: {missing}")
        return list(provided)

    files = []
    for name in COMMON_COMPATIBILITY_NAMES:
        direct = dataset_dir / name
        if direct.exists():
            files.append(direct)

    for name in COMMON_COMPATIBILITY_NAMES:
        for match in dataset_dir.rglob(name):
            if match not in files:
                files.append(match)

    if not files:
        files = sorted(dataset_dir.rglob("compatibility*.txt"))

    if not files:
        raise FileNotFoundError(
            "Could not auto-detect compatibility files. Pass --compatibility-files."
        )

    return files


def hf_split_dir(dataset_dir: Path, split_variant: str) -> Path | None:
    candidates = [
        dataset_dir / split_variant,
        dataset_dir / "polyvore-outfits" / split_variant,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    matches = [path for path in dataset_dir.rglob(split_variant) if path.is_dir()]
    return matches[0] if matches else None


def hf_data_dir(dataset_dir: Path, split_variant: str) -> Path | None:
    candidates = [
        dataset_dir / "data" / split_variant,
        dataset_dir / "polyvore-outfits" / "data" / split_variant,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    matches = [
        path
        for path in dataset_dir.rglob(split_variant)
        if path.is_dir() and path.parent.name == "data"
    ]
    return matches[0] if matches else None


def should_use_hf_parquet(args: argparse.Namespace) -> bool:
    if args.data_format == "hf_parquet":
        return True
    if args.data_format == "files":
        return False
    return hf_data_dir(args.dataset_dir, args.polyvore_split) is not None


def normalize_item_id(value) -> str:
    return str(value or "").strip().strip(",")


def infer_outfit_id(item_ids: list[str], fallback: str) -> str:
    if not item_ids:
        return fallback

    prefixes = [
        item_id.rsplit("_", 1)[0]
        for item_id in item_ids
        if "_" in item_id and item_id.rsplit("_", 1)[0]
    ]
    if prefixes and len(set(prefixes)) == 1:
        return prefixes[0]
    return fallback


def split_name_from_path(path: Path) -> str:
    stem = path.stem.lower()
    if "test" in stem:
        return "test"
    if "valid" in stem or "val" in stem:
        return "validation"
    return "train"


def build_hf_token_map(dataset_dir: Path, split_variant: str) -> dict[str, str]:
    split_dir = hf_split_dir(dataset_dir, split_variant)
    if split_dir is None:
        return {}

    token_map = {}
    for json_name in ["train.json", "valid.json", "validation.json", "test.json"]:
        path = split_dir / json_name
        if not path.exists():
            continue

        outfits = read_json(path)
        if not isinstance(outfits, list):
            continue

        for outfit in outfits:
            if not isinstance(outfit, dict):
                continue
            set_id = normalize_item_id(outfit.get("set_id", outfit.get("id")))
            items = outfit.get("items", [])
            if not set_id or not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                item_id = normalize_item_id(item.get("item_id", item.get("id")))
                index = normalize_item_id(item.get("index"))
                if item_id:
                    token_map[item_id] = item_id
                if set_id and index and item_id:
                    token_map[f"{set_id}_{index}"] = item_id

    print(f"HF token map size: {len(token_map)}")
    return token_map


def parse_text_compatibility_file(
    path: Path,
    token_map: dict[str, str] | None = None,
) -> list[Outfit]:
    outfits = []
    split_name = split_name_from_path(path)
    token_map = token_map or {}

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        tokens = line.replace(",", " ").split()
        if len(tokens) < 3:
            continue

        try:
            label = int(float(tokens[0]))
        except ValueError:
            continue

        raw_item_tokens = [normalize_item_id(token) for token in tokens[1:]]
        item_ids = tuple(
            token_map.get(token, token)
            for token in raw_item_tokens
            if token_map.get(token, token)
        )
        if len(item_ids) < 2:
            continue

        fallback = f"{path.stem}_{line_number}"
        outfits.append(
            Outfit(
                outfit_id=infer_outfit_id(raw_item_tokens, fallback),
                item_ids=item_ids,
                label=1 if label == 1 else 0,
                source_split=split_name,
            )
        )

    return outfits


def item_ids_from_json_item(item) -> list[str]:
    if isinstance(item, str):
        return [normalize_item_id(item)]
    if not isinstance(item, dict):
        return []

    for key in ["item_id", "id", "product_id"]:
        if key in item:
            return [normalize_item_id(item[key])]

    return []


def parse_json_compatibility_file(path: Path) -> list[Outfit]:
    payload = read_json(path)
    if isinstance(payload, dict):
        for key in ["outfits", "data", "items"]:
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break

    if not isinstance(payload, list):
        return []

    outfits = []
    split_name = split_name_from_path(path)
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            continue

        raw_label = entry.get("label", entry.get("compatible", entry.get("compatibility")))
        if raw_label is None:
            raw_label = 1
        label = 1 if int(bool(raw_label)) == 1 else 0

        raw_items = (
            entry.get("item_ids")
            or entry.get("items")
            or entry.get("products")
            or entry.get("question")
        )
        if not isinstance(raw_items, list):
            continue

        item_ids = []
        for raw_item in raw_items:
            item_ids.extend(item_ids_from_json_item(raw_item))

        item_ids = tuple(item_id for item_id in item_ids if item_id)
        if len(item_ids) < 2:
            continue

        outfit_id = str(
            entry.get("set_id")
            or entry.get("outfit_id")
            or entry.get("id")
            or infer_outfit_id(list(item_ids), f"{path.stem}_{index}")
        )
        outfits.append(
            Outfit(
                outfit_id=outfit_id,
                item_ids=item_ids,
                label=label,
                source_split=split_name,
            )
        )

    return outfits


def load_outfits(paths: list[Path], token_map: dict[str, str] | None = None) -> list[Outfit]:
    outfits = []
    for path in paths:
        if path.suffix.lower() == ".json":
            parsed = parse_json_compatibility_file(path)
        else:
            parsed = parse_text_compatibility_file(path, token_map=token_map)
        print(f"Loaded {len(parsed)} outfits from {path}")
        outfits.extend(parsed)
    return outfits


def load_metadata(path: Path) -> dict[str, dict]:
    payload = read_json(path)
    if isinstance(payload, list):
        metadata = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            item_id = item.get("item_id", item.get("id", item.get("product_id")))
            if item_id is not None:
                metadata[normalize_item_id(item_id)] = item
        return metadata

    if isinstance(payload, dict):
        if "items" in payload and isinstance(payload["items"], list):
            return {
                normalize_item_id(item.get("item_id", item.get("id", item.get("product_id")))): item
                for item in payload["items"]
                if isinstance(item, dict)
                and item.get("item_id", item.get("id", item.get("product_id"))) is not None
            }

        return {
            normalize_item_id(key): value
            for key, value in payload.items()
            if isinstance(value, dict)
        }

    raise ValueError(f"Unsupported metadata format: {path}")


def metadata_lookup(metadata: dict[str, dict], item_id: str) -> dict:
    candidates = [item_id]
    if "_" in item_id:
        candidates.append(item_id.split("_")[-1])
    for candidate in candidates:
        if candidate in metadata:
            return metadata[candidate]
    return {}


def normalize_text(value) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def direct_category_from_text(value: str) -> str | None:
    normalized = normalize_text(value)
    if normalized in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[normalized]

    tokens = normalized.replace("/", " ").split()
    for token in tokens:
        if token in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[token]

    for terms, category in TEXT_CATEGORY_HINTS:
        if any(term in normalized for term in terms):
            return category

    return None


def category_for_item(item_id: str, metadata: dict[str, dict]) -> str | None:
    item = metadata_lookup(metadata, item_id)
    fields = [
        "category",
        "category_name",
        "semantic_category",
        "fine_category",
        "coarse_category",
        "product_type",
        "item_type",
        "title",
        "name",
        "description",
    ]

    for field in fields:
        category = direct_category_from_text(item.get(field))
        if category in TARGET_CATEGORIES:
            return category

    combined = " ".join(str(item.get(field, "")) for field in fields)
    return direct_category_from_text(combined)


def image_bytes_from_value(value) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, dict):
        raw = value.get("bytes")
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, bytearray):
            return bytes(raw)
    return None


def load_hf_parquet_items(
    dataset_dir: Path,
    split_variant: str,
    required_item_ids: set[str],
) -> tuple[dict[str, dict], dict[str, bytes]]:
    data_dir = hf_data_dir(dataset_dir, split_variant)
    if data_dir is None:
        raise FileNotFoundError(
            f"Could not find Hugging Face parquet data/{split_variant} folder."
        )

    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "Hugging Face parquet mode requires pandas and pyarrow. "
            "In Colab run: pip install pandas pyarrow"
        ) from exc

    parquet_names = [
        "train.parquet",
        "valid.parquet",
        "validation.parquet",
        "test.parquet",
    ]
    metadata_updates = {}
    image_sources = {}

    print(f"Loading HF parquet items from {data_dir}")
    for parquet_name in parquet_names:
        path = data_dir / parquet_name
        if not path.exists():
            continue

        dataframe = pd.read_parquet(path)
        if "item_id" not in dataframe.columns:
            continue

        dataframe["item_id"] = dataframe["item_id"].astype(str)
        if required_item_ids:
            dataframe = dataframe[dataframe["item_id"].isin(required_item_ids)]

        print(f"  {parquet_name}: {len(dataframe)} required item rows")
        for row in dataframe.to_dict("records"):
            item_id = normalize_item_id(row.get("item_id"))
            if not item_id:
                continue

            image_bytes = image_bytes_from_value(row.get("image"))
            if image_bytes:
                image_sources[f"item-bytes:{item_id}"] = image_bytes

            metadata_row = {
                key: value
                for key, value in row.items()
                if key != "image" and not isinstance(value, (bytes, bytearray))
            }
            metadata_updates[item_id] = metadata_row

    print(f"Loaded {len(image_sources)} HF parquet image byte records")
    return metadata_updates, image_sources


def build_image_index(image_dir: Path) -> dict[str, Path]:
    print(f"Indexing images under {image_dir} ...")
    start_time = time.time()
    index = {}
    for pattern in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        for path in image_dir.rglob(pattern):
            index.setdefault(path.stem, path)
            index.setdefault(path.name, path)
    print(f"Indexed {len(index)} image keys in {time.time() - start_time:.1f}s")
    return index


def image_path_from_metadata(item: dict, dataset_dir: Path, image_dir: Path) -> Path | None:
    for key in ["image_path", "path", "filename", "file_name", "image", "image_file"]:
        value = item.get(key)
        if not value:
            continue

        candidate = Path(str(value))
        candidates = [
            candidate,
            dataset_dir / candidate,
            image_dir / candidate,
            image_dir / candidate.name,
        ]
        for path in candidates:
            if path.exists():
                return path

    return None


def image_path_for_item(
    item_id: str,
    metadata: dict[str, dict],
    dataset_dir: Path,
    image_dir: Path,
    image_index: dict[str, Path],
    image_sources: dict[str, bytes] | None = None,
) -> str | Path | None:
    image_sources = image_sources or {}
    byte_ref = f"item-bytes:{item_id}"
    if byte_ref in image_sources:
        return byte_ref

    item = metadata_lookup(metadata, item_id)
    from_metadata = image_path_from_metadata(item, dataset_dir, image_dir)
    if from_metadata:
        return from_metadata

    candidates = [item_id]
    if "_" in item_id:
        candidates.append(item_id.split("_")[-1])

    for candidate in candidates:
        if candidate in image_index:
            return image_index[candidate]
        for suffix in [".jpg", ".jpeg", ".png", ".webp"]:
            key = f"{candidate}{suffix}"
            if key in image_index:
                return image_index[key]

    return None


def are_complementary(left_category: str, right_category: str) -> bool:
    return (
        right_category in COMPLEMENTARY_CATEGORIES.get(left_category, set())
        or left_category in COMPLEMENTARY_CATEGORIES.get(right_category, set())
    )


def item_records_for_outfit(
    outfit: Outfit,
    metadata: dict[str, dict],
    dataset_dir: Path,
    image_dir: Path,
    image_index: dict[str, Path],
    image_sources: dict[str, bytes] | None = None,
) -> list[ItemRecord]:
    records = []
    seen = set()
    for item_id in outfit.item_ids:
        if item_id in seen:
            continue
        seen.add(item_id)

        category = category_for_item(item_id, metadata)
        if category not in TARGET_CATEGORIES:
            continue

        image_path = image_path_for_item(
            item_id,
            metadata,
            dataset_dir,
            image_dir,
            image_index,
            image_sources=image_sources,
        )
        if not image_path:
            continue

        records.append(
            ItemRecord(
                item_id=item_id,
                outfit_id=outfit.outfit_id,
                category=category,
                image_path=str(image_path),
            )
        )

    return records


def split_positive_outfits(
    positive_outfits: list[Outfit],
    seed: int,
) -> dict[str, list[Outfit]]:
    by_source = defaultdict(list)
    for outfit in positive_outfits:
        by_source[outfit.source_split].append(outfit)

    if by_source.get("validation") and by_source.get("test"):
        return {
            "train": by_source.get("train", []),
            "validation": by_source.get("validation", []),
            "test": by_source.get("test", []),
        }

    train, temp = train_test_split(
        positive_outfits,
        test_size=0.30,
        random_state=seed,
    )
    validation, test = train_test_split(
        temp,
        test_size=0.50,
        random_state=seed,
    )
    return {"train": train, "validation": validation, "test": test}


def positive_pairs_from_records(
    records_by_outfit: dict[str, list[ItemRecord]],
    split_name: str,
    max_pairs_per_outfit: int,
    rng: random.Random,
) -> list[PairRecord]:
    pairs = []
    for records in records_by_outfit.values():
        combinations = [
            pair
            for pair in itertools.combinations(records, 2)
            if are_complementary(pair[0].category, pair[1].category)
        ]
        rng.shuffle(combinations)
        for left, right in combinations[:max_pairs_per_outfit]:
            pairs.append(
                PairRecord(
                    left_item_id=left.item_id,
                    right_item_id=right.item_id,
                    left_image_path=left.image_path,
                    right_image_path=right.image_path,
                    left_category=left.category,
                    right_category=right.category,
                    label=1,
                    split=split_name,
                )
            )
    return pairs


def negative_pairs_from_records(
    records_by_outfit: dict[str, list[ItemRecord]],
    split_name: str,
    target_count: int,
    rng: random.Random,
) -> list[PairRecord]:
    records_by_category = defaultdict(list)
    for records in records_by_outfit.values():
        for record in records:
            records_by_category[record.category].append(record)

    category_pairs = [
        (left, right)
        for left in TARGET_CATEGORIES
        for right in TARGET_CATEGORIES
        if left < right and are_complementary(left, right)
        and records_by_category.get(left)
        and records_by_category.get(right)
    ]
    if not category_pairs:
        return []

    pairs = []
    seen = set()
    attempts = 0
    max_attempts = max(target_count * 50, 1000)

    while len(pairs) < target_count and attempts < max_attempts:
        attempts += 1
        left_category, right_category = rng.choice(category_pairs)
        left = rng.choice(records_by_category[left_category])
        right = rng.choice(records_by_category[right_category])
        if left.outfit_id == right.outfit_id:
            continue

        key = tuple(sorted([left.item_id, right.item_id]))
        if key in seen:
            continue
        seen.add(key)

        pairs.append(
            PairRecord(
                left_item_id=left.item_id,
                right_item_id=right.item_id,
                left_image_path=left.image_path,
                right_image_path=right.image_path,
                left_category=left.category,
                right_category=right.category,
                label=0,
                split=split_name,
            )
        )

    return pairs


def build_pairs(
    split_outfits: dict[str, list[Outfit]],
    metadata: dict[str, dict],
    dataset_dir: Path,
    image_dir: Path,
    image_index: dict[str, Path],
    image_sources: dict[str, bytes] | None,
    max_pairs_per_outfit: int,
    negative_ratio: float,
    seed: int,
) -> list[PairRecord]:
    rng = random.Random(seed)
    all_pairs = []

    for split_name, outfits in split_outfits.items():
        records_by_outfit = {}
        for outfit in outfits:
            records = item_records_for_outfit(
                outfit,
                metadata,
                dataset_dir,
                image_dir,
                image_index,
                image_sources=image_sources,
            )
            if len(records) >= 2:
                records_by_outfit[outfit.outfit_id] = records

        positive_pairs = positive_pairs_from_records(
            records_by_outfit,
            split_name,
            max_pairs_per_outfit,
            rng,
        )
        negative_pairs = negative_pairs_from_records(
            records_by_outfit,
            split_name,
            target_count=int(len(positive_pairs) * negative_ratio),
            rng=rng,
        )

        print(
            f"{split_name}: {len(records_by_outfit)} usable outfits, "
            f"{len(positive_pairs)} positive pairs, {len(negative_pairs)} negative pairs"
        )
        all_pairs.extend(positive_pairs)
        all_pairs.extend(negative_pairs)

    rng.shuffle(all_pairs)
    return all_pairs


def load_image(path: str, image_sources: dict[str, bytes] | None = None, image_size=None):
    image_sources = image_sources or {}
    if path.startswith("item-bytes:"):
        image = Image.open(io.BytesIO(image_sources[path])).convert("RGB")
    else:
        image = Image.open(path).convert("RGB")

    if image_size:
        image.thumbnail((image_size, image_size))
    return image


def encode_clip(
    image_paths: list[str],
    image_sources: dict[str, bytes],
    model_name: str,
    batch_size: int,
) -> dict[str, np.ndarray]:
    import clip
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)
    model.eval()

    embeddings = {}
    batch_images = []
    batch_paths = []
    start_time = time.time()

    for path in image_paths:
        try:
            batch_images.append(preprocess(load_image(path, image_sources=image_sources)))
            batch_paths.append(path)
        except Exception:
            continue

        if len(batch_images) == batch_size:
            embeddings.update(encode_clip_batch(model, batch_images, batch_paths, device))
            batch_images = []
            batch_paths = []
            if len(embeddings) % (batch_size * 10) == 0:
                print(f"Embedded {len(embeddings)} images in {time.time() - start_time:.1f}s")

    if batch_images:
        embeddings.update(encode_clip_batch(model, batch_images, batch_paths, device))

    return embeddings


def encode_clip_batch(model, batch_images, batch_paths, device: str) -> dict[str, np.ndarray]:
    import torch

    image_input = torch.stack(batch_images).to(device)
    with torch.no_grad():
        features = model.encode_image(image_input)
        features = features / features.norm(dim=-1, keepdim=True)
    matrix = features.cpu().numpy()
    return {path: matrix[index] for index, path in enumerate(batch_paths)}


def encode_dinov2(
    image_paths: list[str],
    image_sources: dict[str, bytes],
    model_name: str,
    batch_size: int,
) -> dict[str, np.ndarray]:
    import torch
    from transformers import AutoImageProcessor, AutoModel

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    embeddings = {}
    batch_images = []
    batch_paths = []
    start_time = time.time()

    for path in image_paths:
        try:
            batch_images.append(load_image(path, image_sources=image_sources))
            batch_paths.append(path)
        except Exception:
            continue

        if len(batch_images) == batch_size:
            embeddings.update(encode_dinov2_batch(model, processor, batch_images, batch_paths, device))
            batch_images = []
            batch_paths = []
            if len(embeddings) % (batch_size * 10) == 0:
                print(f"Embedded {len(embeddings)} images in {time.time() - start_time:.1f}s")

    if batch_images:
        embeddings.update(encode_dinov2_batch(model, processor, batch_images, batch_paths, device))

    return embeddings


def encode_dinov2_batch(model, processor, batch_images, batch_paths, device: str) -> dict[str, np.ndarray]:
    import torch

    inputs = processor(images=batch_images, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        features = getattr(outputs, "pooler_output", None)
        if features is None:
            features = outputs.last_hidden_state[:, 0]
        features = features / features.norm(dim=-1, keepdim=True)
    matrix = features.cpu().numpy()
    return {path: matrix[index] for index, path in enumerate(batch_paths)}


def extract_embeddings(
    pairs: list[PairRecord],
    image_sources: dict[str, bytes],
    feature_extractor: str,
    clip_model: str,
    hf_model: str,
    batch_size: int,
) -> dict[str, np.ndarray]:
    image_paths = sorted(
        {
            pair.left_image_path
            for pair in pairs
        }
        | {
            pair.right_image_path
            for pair in pairs
        }
    )
    print(f"Extracting {feature_extractor} embeddings for {len(image_paths)} unique images")

    if feature_extractor == "clip":
        return encode_clip(image_paths, image_sources, clip_model, batch_size)
    if feature_extractor == "dinov2":
        return encode_dinov2(image_paths, image_sources, hf_model, batch_size)
    raise ValueError(f"Unsupported feature extractor: {feature_extractor}")


def pair_features(left_embedding: np.ndarray, right_embedding: np.ndarray) -> np.ndarray:
    return np.concatenate(
        [
            left_embedding,
            right_embedding,
            np.abs(left_embedding - right_embedding),
            left_embedding * right_embedding,
        ]
    )


def build_matrix(
    pairs: list[PairRecord],
    embeddings: dict[str, np.ndarray],
    augment_swap: bool,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    features = []
    labels = []
    rows = []

    for pair in pairs:
        left_embedding = embeddings.get(pair.left_image_path)
        right_embedding = embeddings.get(pair.right_image_path)
        if left_embedding is None or right_embedding is None:
            continue

        features.append(pair_features(left_embedding, right_embedding))
        labels.append(pair.label)
        rows.append(pair.__dict__)

        if augment_swap:
            features.append(pair_features(right_embedding, left_embedding))
            labels.append(pair.label)
            swapped = dict(pair.__dict__)
            swapped["left_item_id"], swapped["right_item_id"] = (
                swapped["right_item_id"],
                swapped["left_item_id"],
            )
            swapped["left_image_path"], swapped["right_image_path"] = (
                swapped["right_image_path"],
                swapped["left_image_path"],
            )
            swapped["left_category"], swapped["right_category"] = (
                swapped["right_category"],
                swapped["left_category"],
            )
            rows.append(swapped)

    if not features:
        raise RuntimeError("No pair features could be built.")

    return np.vstack(features), np.array(labels), rows


def classifier_candidates(args: argparse.Namespace) -> dict[str, Pipeline]:
    candidates = {}
    if "logreg" in args.models:
        candidates["logreg"] = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        solver="lbfgs",
                    ),
                ),
            ]
        )

    if "linear_svm" in args.models:
        candidates["linear_svm"] = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    CalibratedClassifierCV(
                        LinearSVC(class_weight="balanced", max_iter=5000),
                        method="sigmoid",
                        cv=3,
                    ),
                ),
            ]
        )

    if "random_forest" in args.models:
        candidates["random_forest"] = Pipeline(
            [
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=args.random_forest_estimators,
                        class_weight="balanced",
                        random_state=args.seed,
                        n_jobs=-1,
                    ),
                )
            ]
        )

    if "mlp" in args.models:
        candidates["mlp"] = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    MLPClassifier(
                        hidden_layer_sizes=(256, 64),
                        activation="relu",
                        alpha=0.0005,
                        learning_rate_init=0.001,
                        max_iter=args.mlp_max_iter,
                        early_stopping=False,
                        random_state=args.seed,
                    ),
                ),
            ]
        )

    return candidates


def positive_probability(model, x_values: np.ndarray) -> np.ndarray | None:
    if not hasattr(model, "predict_proba"):
        return None

    probabilities = model.predict_proba(x_values)
    classes = list(model.classes_)
    if 1 not in classes:
        return None
    return probabilities[:, classes.index(1)]


def evaluate_model(model, x_values: np.ndarray, y_true: np.ndarray) -> dict:
    predictions = model.predict(x_values)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        predictions,
        average="macro",
        zero_division=0,
    )
    report = classification_report(
        y_true,
        predictions,
        labels=[0, 1],
        target_names=["incompatible", "compatible"],
        output_dict=True,
        zero_division=0,
    )

    probability = positive_probability(model, x_values)
    roc_auc = None
    if probability is not None and len(set(y_true.tolist())) > 1:
        roc_auc = float(roc_auc_score(y_true, probability))

    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(f1),
        "compatible_precision": float(report["compatible"]["precision"]),
        "compatible_recall": float(report["compatible"]["recall"]),
        "compatible_f1": float(report["compatible"]["f1-score"]),
        "roc_auc": roc_auc,
        "classification_report": report,
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=[0, 1]).tolist(),
    }


def train_and_compare(
    args: argparse.Namespace,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
):
    comparison = []
    trained_models = {}

    for model_name, model in classifier_candidates(args).items():
        print(f"\nTraining classifier: {model_name}")
        start_time = time.time()
        model.fit(x_train, y_train)
        training_time = time.time() - start_time

        validation_metrics = evaluate_model(model, x_val, y_val)
        test_metrics = evaluate_model(model, x_test, y_test)
        trained_models[model_name] = model
        comparison.append(
            {
                "model": model_name,
                "training_time_seconds": round(training_time, 3),
                "validation_accuracy": validation_metrics["accuracy"],
                "validation_macro_f1": validation_metrics["macro_f1"],
                "validation_compatible_f1": validation_metrics["compatible_f1"],
                "validation_roc_auc": validation_metrics["roc_auc"],
                "test_accuracy": test_metrics["accuracy"],
                "test_macro_f1": test_metrics["macro_f1"],
                "test_compatible_f1": test_metrics["compatible_f1"],
                "test_roc_auc": test_metrics["roc_auc"],
                "validation": validation_metrics,
                "test": test_metrics,
            }
        )
        print(
            f"{model_name}: val acc {validation_metrics['accuracy'] * 100:.2f}% "
            f"macro F1 {validation_metrics['macro_f1']:.3f} "
            f"compatible F1 {validation_metrics['compatible_f1']:.3f} | "
            f"test acc {test_metrics['accuracy'] * 100:.2f}% "
            f"macro F1 {test_metrics['macro_f1']:.3f}"
        )

    def selection_value(row):
        value = row.get(args.selection_metric)
        return -1 if value is None else value

    best_row = max(comparison, key=selection_value)
    best_name = best_row["model"]
    return best_name, trained_models[best_name], best_row, comparison


def maybe_refit_model(args, model_name, x_train_val, y_train_val):
    model = classifier_candidates(args)[model_name]
    model.fit(x_train_val, y_train_val)
    return model


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        keys = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        fieldnames = keys

    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pair_label_counts(rows: list[dict]) -> dict[tuple[str, int], int]:
    counts = defaultdict(int)
    for row in rows:
        counts[(row["split"], int(row["label"]))] += 1
    return dict(counts)


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    use_hf_parquet = should_use_hf_parquet(args)
    metadata_path = find_metadata_file(args.dataset_dir, args.metadata_file)
    image_dir = find_image_dir(args.dataset_dir, args.image_dir)
    compatibility_search_dir = (
        hf_split_dir(args.dataset_dir, args.polyvore_split)
        if use_hf_parquet
        else args.dataset_dir
    ) or args.dataset_dir
    compatibility_files = find_compatibility_files(
        compatibility_search_dir,
        args.compatibility_files,
    )
    token_map = build_hf_token_map(args.dataset_dir, args.polyvore_split) if use_hf_parquet else {}

    print(f"Metadata: {metadata_path}")
    print(f"Data format: {'hf_parquet' if use_hf_parquet else 'files'}")
    print(f"Images: {image_dir}")
    print("Compatibility files:")
    for path in compatibility_files:
        print(f"  - {path}")

    metadata = load_metadata(metadata_path)
    outfits = load_outfits(compatibility_files, token_map=token_map)
    positive_outfits = [outfit for outfit in outfits if outfit.label == 1]
    if args.max_positive_outfits and len(positive_outfits) > args.max_positive_outfits:
        positive_outfits = random.sample(positive_outfits, args.max_positive_outfits)

    print(f"Metadata items: {len(metadata)}")
    print(f"Total outfits: {len(outfits)}")
    print(f"Compatible outfits selected: {len(positive_outfits)}")

    split_outfits = split_positive_outfits(positive_outfits, args.seed)
    print(
        "Outfit split counts:",
        {split_name: len(items) for split_name, items in split_outfits.items()},
    )

    selected_item_ids = {
        item_id
        for split_items in split_outfits.values()
        for outfit in split_items
        for item_id in outfit.item_ids
    }
    image_sources = {}
    if use_hf_parquet:
        parquet_metadata, image_sources = load_hf_parquet_items(
            args.dataset_dir,
            args.polyvore_split,
            selected_item_ids,
        )
        for item_id, row in parquet_metadata.items():
            merged = dict(metadata.get(item_id, {}))
            merged.update(row)
            metadata[item_id] = merged

    image_index = {} if use_hf_parquet else build_image_index(image_dir)

    pairs = build_pairs(
        split_outfits,
        metadata,
        args.dataset_dir,
        image_dir,
        image_index,
        image_sources,
        args.max_pairs_per_outfit,
        args.negative_ratio,
        args.seed,
    )
    if args.max_pairs and len(pairs) > args.max_pairs:
        pairs = random.sample(pairs, args.max_pairs)

    pair_rows = [pair.__dict__ for pair in pairs]
    write_csv(args.output_dir / "polyvore_pairs.csv", pair_rows)
    print("Pair label counts:")
    for (split_name, label), count in sorted(pair_label_counts(pair_rows).items()):
        print(f"  {split_name} label={label}: {count}")

    embeddings = extract_embeddings(
        pairs,
        image_sources,
        args.feature_extractor,
        args.clip_model,
        args.hf_model,
        args.batch_size,
    )

    matrices = {}
    for split_name in ["train", "validation", "test"]:
        split_pairs = [pair for pair in pairs if pair.split == split_name]
        augment = split_name == "train"
        matrices[split_name] = build_matrix(split_pairs, embeddings, augment_swap=augment)
        print(
            f"{split_name}: matrix {matrices[split_name][0].shape}, "
            f"labels {np.bincount(matrices[split_name][1].astype(int), minlength=2).tolist()}"
        )

    x_train, y_train, train_rows = matrices["train"]
    x_val, y_val, validation_rows = matrices["validation"]
    x_test, y_test, test_rows = matrices["test"]

    best_name, model, best_row, comparison = train_and_compare(
        args,
        x_train,
        y_train,
        x_val,
        y_val,
        x_test,
        y_test,
    )

    saved_model = model
    if args.refit_train_val:
        print(f"Refitting selected model on train+validation: {best_name}")
        saved_model = maybe_refit_model(
            args,
            best_name,
            np.vstack([x_train, x_val]),
            np.concatenate([y_train, y_val]),
        )

    artifact = {
        "model": saved_model,
        "model_name": best_name,
        "feature_extractor": args.feature_extractor,
        "clip_model": args.clip_model if args.feature_extractor == "clip" else None,
        "hf_model": args.hf_model if args.feature_extractor == "dinov2" else None,
        "pair_feature_schema": [
            "left_embedding",
            "right_embedding",
            "absolute_difference",
            "elementwise_product",
        ],
        "category_pair_strategy": "compatible_outfit_positives_cross_outfit_negatives",
        "selection_metric": args.selection_metric,
        "refit_train_val": bool(args.refit_train_val),
        "train_count": int(len(y_train)),
        "validation_count": int(len(y_val)),
        "test_count": int(len(y_test)),
        "metrics": {
            "validation": best_row["validation"],
            "test": best_row["test"],
        },
    }
    model_path = args.output_dir / "polyvore_compatibility_model.joblib"
    joblib.dump(artifact, model_path)

    comparison_public = [
        {
            key: value
            for key, value in row.items()
            if key not in {"validation", "test"}
        }
        for row in comparison
    ]
    write_csv(args.output_dir / "polyvore_model_comparison.csv", comparison_public)
    write_csv(args.output_dir / "polyvore_train_pairs_used.csv", train_rows)
    write_csv(args.output_dir / "polyvore_validation_pairs_used.csv", validation_rows)
    write_csv(args.output_dir / "polyvore_test_pairs_used.csv", test_rows)

    metrics_payload = {
        "dataset_dir": str(args.dataset_dir),
        "metadata_path": str(metadata_path),
        "data_format": "hf_parquet" if use_hf_parquet else "files",
        "polyvore_split": args.polyvore_split,
        "image_dir": str(image_dir),
        "compatibility_files": [str(path) for path in compatibility_files],
        "feature_extractor": args.feature_extractor,
        "clip_model": args.clip_model if args.feature_extractor == "clip" else None,
        "hf_model": args.hf_model if args.feature_extractor == "dinov2" else None,
        "selected_model": best_name,
        "selection_metric": args.selection_metric,
        "metadata_item_count": int(len(metadata)),
        "outfit_count": int(len(outfits)),
        "compatible_outfits_selected": int(len(positive_outfits)),
        "pair_count": int(len(pair_rows)),
        "pair_label_counts": {
            f"{split}_{label}": int(count)
            for (split, label), count in pair_label_counts(pair_rows).items()
        },
        "train_count": int(len(y_train)),
        "validation_count": int(len(y_val)),
        "test_count": int(len(y_test)),
        "best_validation": best_row["validation"],
        "best_test": best_row["test"],
        "comparison": comparison_public,
    }
    save_json(args.output_dir / "polyvore_metrics.json", metrics_payload)

    print(f"\nSaved model: {model_path}")
    print(f"Saved metrics: {args.output_dir / 'polyvore_metrics.json'}")
    print(f"Saved comparison: {args.output_dir / 'polyvore_model_comparison.csv'}")
    print(f"Best model by {args.selection_metric}: {best_name}")
    print(
        "Validation accuracy:",
        f"{best_row['validation']['accuracy'] * 100:.2f}%",
        "macro F1:",
        f"{best_row['validation']['macro_f1']:.3f}",
        "compatible F1:",
        f"{best_row['validation']['compatible_f1']:.3f}",
    )
    print(
        "Test accuracy:",
        f"{best_row['test']['accuracy'] * 100:.2f}%",
        "macro F1:",
        f"{best_row['test']['macro_f1']:.3f}",
        "compatible F1:",
        f"{best_row['test']['compatible_f1']:.3f}",
    )
    if args.feature_extractor != "clip":
        print(
            "Note: this artifact is for comparison. The current AI service "
            "uses CLIP embeddings for compatibility scoring."
        )


if __name__ == "__main__":
    main()
