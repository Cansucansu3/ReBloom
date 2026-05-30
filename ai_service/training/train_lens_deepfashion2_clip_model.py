"""
Train a ReBloom Lens category classifier on a DeepFashion2 subset using CLIP.

This script does not fine-tune CLIP. It uses CLIP ViT-B/32 as a frozen image
feature extractor and trains a supervised classifier on top of the embeddings.

Expected DeepFashion2 files:
    train/image/*.jpg
    train/annos/*.json
    validation/image/*.jpg
    validation/annos/*.json

The script reads category labels from the DeepFashion2 annotation JSON files.
If an image contains multiple clothing items, the largest item bounding box is
used as the image-level category label for this Lens classifier.

Example:
    python train_lens_deepfashion2_clip_model.py \
        --dataset-dir /kaggle/input/deep-fashion \
        --output-dir /kaggle/working/rebloom_lens_deepfashion2_model \
        --max-samples 50000
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import clip
import joblib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


TARGET_CLASSES = [
    "tops",
    "pants",
    "shorts",
    "skirts",
    "dresses",
    "outerwear",
]

DEEPFASHION2_CATEGORY_MAP = {
    "short sleeve top": "tops",
    "long sleeve top": "tops",
    "short sleeved shirt": "tops",
    "long sleeved shirt": "tops",
    "short_sleeved_shirt": "tops",
    "long_sleeved_shirt": "tops",
    "short sleeve outwear": "outerwear",
    "long sleeve outwear": "outerwear",
    "short sleeved outwear": "outerwear",
    "long sleeved outwear": "outerwear",
    "short_sleeved_outwear": "outerwear",
    "long_sleeved_outwear": "outerwear",
    "vest": "tops",
    "sling": "tops",
    "shorts": "shorts",
    "trousers": "pants",
    "skirt": "skirts",
    "short sleeve dress": "dresses",
    "long sleeve dress": "dresses",
    "short sleeved dress": "dresses",
    "long sleeved dress": "dresses",
    "short_sleeved_dress": "dresses",
    "long_sleeved_dress": "dresses",
    "vest dress": "dresses",
    "vest_dress": "dresses",
    "sling dress": "dresses",
    "sling_dress": "dresses",
}

CATEGORY_ID_TO_NAME = {
    1: "short_sleeved_shirt",
    2: "long_sleeved_shirt",
    3: "short_sleeved_outwear",
    4: "long_sleeved_outwear",
    5: "vest",
    6: "sling",
    7: "shorts",
    8: "trousers",
    9: "skirt",
    10: "short_sleeved_dress",
    11: "long_sleeved_dress",
    12: "vest_dress",
    13: "sling_dress",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("/kaggle/input/deep-fashion"),
        help="DeepFashion2 root folder.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/kaggle/working/rebloom_lens_deepfashion2_model"),
        help="Output folder for model and metrics.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=50000,
        help="Maximum total image count after category mapping. Use 0 for all.",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=0,
        help="Optional balanced cap per ReBloom class. Use 0 to derive from max-samples.",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clip-model", default="ViT-B/32")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["logreg", "linear_svm", "random_forest", "mlp"],
        choices=["logreg", "linear_svm", "random_forest", "mlp"],
        help="Classifier algorithms to compare on the same CLIP embeddings.",
    )
    parser.add_argument("--random-forest-estimators", type=int, default=150)
    parser.add_argument("--mlp-max-iter", type=int, default=200)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def find_split_dir(dataset_dir: Path, split_name: str) -> Path | None:
    candidates = [
        dataset_dir / split_name,
        dataset_dir / "DeepFashion2" / split_name,
        dataset_dir / "deepfashion2" / split_name,
    ]
    for candidate in candidates:
        if (candidate / "image").exists() and (candidate / "annos").exists():
            return candidate

    for candidate in dataset_dir.rglob(split_name):
        if candidate.is_dir() and (candidate / "image").exists() and (candidate / "annos").exists():
            return candidate

    return None


def bbox_area(bounding_box) -> float:
    if not bounding_box or len(bounding_box) != 4:
        return 0
    x1, y1, x2, y2 = bounding_box
    return max(0, float(x2) - float(x1)) * max(0, float(y2) - float(y1))


def best_item_from_annotation(annotation: dict) -> dict | None:
    items = [
        value
        for key, value in annotation.items()
        if key.startswith("item") and isinstance(value, dict)
    ]
    if not items:
        return None
    return max(items, key=lambda item: bbox_area(item.get("bounding_box")))


def category_name_from_item(item: dict) -> str:
    category_name = item.get("category_name")
    if category_name:
        return str(category_name).strip()
    category_id = item.get("category_id")
    try:
        return CATEGORY_ID_TO_NAME.get(int(category_id), "")
    except Exception:
        return ""


def normalize_deepfashion_category(value: str) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def image_path_for_annotation(image_dir: Path, annotation_path: Path) -> Path | None:
    stem = annotation_path.stem
    for suffix in [".jpg", ".jpeg", ".png"]:
        candidate = image_dir / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def collect_split_rows(split_dir: Path, split_name: str) -> list[dict]:
    image_dir = split_dir / "image"
    annotation_dir = split_dir / "annos"
    rows = []

    for annotation_path in annotation_dir.glob("*.json"):
        try:
            annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        item = best_item_from_annotation(annotation)
        if not item:
            continue

        deepfashion_category = category_name_from_item(item)
        rebloom_category = DEEPFASHION2_CATEGORY_MAP.get(
            normalize_deepfashion_category(deepfashion_category)
        )
        if rebloom_category not in TARGET_CLASSES:
            continue

        image_path = image_path_for_annotation(image_dir, annotation_path)
        if image_path is None:
            continue

        rows.append(
            {
                "image_name": image_path.name,
                "image_path": image_path,
                "annotation_path": annotation_path,
                "split": split_name,
                "deepfashion_category": deepfashion_category,
                "rebloom_category": rebloom_category,
                "bbox_area": bbox_area(item.get("bounding_box")),
                "source": annotation.get("source"),
                "pair_id": annotation.get("pair_id"),
            }
        )

    return rows


def build_curated_dataframe(
    dataset_dir: Path,
    max_samples: int,
    max_per_class: int,
    seed: int,
) -> pd.DataFrame:
    rows = []
    for split_name in ["train", "validation"]:
        split_dir = find_split_dir(dataset_dir, split_name)
        if split_dir is None:
            print(f"Warning: could not find {split_name}/image and {split_name}/annos")
            continue
        print(f"Using {split_name} split: {split_dir}")
        rows.extend(collect_split_rows(split_dir, split_name))

    if not rows:
        raise RuntimeError("No DeepFashion2 rows found.")

    dataframe = pd.DataFrame(rows)

    if max_per_class <= 0 and max_samples > 0:
        max_per_class = max(1, max_samples // len(TARGET_CLASSES))

    selected = []
    for category, group in dataframe.groupby("rebloom_category"):
        cap = max_per_class if max_per_class > 0 else len(group)
        if len(group) > cap:
            group = group.sample(cap, random_state=seed)
        selected.append(group)

    curated = pd.concat(selected).sample(frac=1, random_state=seed).reset_index(drop=True)
    if max_samples > 0 and len(curated) > max_samples:
        curated = curated.sample(max_samples, random_state=seed).reset_index(drop=True)
    return curated


def load_image_tensor(path: Path, preprocess):
    try:
        image = Image.open(path).convert("RGB")
        return preprocess(image)
    except Exception:
        return None


def encode_batch(model, batch_tensors, device: str) -> np.ndarray:
    image_input = torch.stack(batch_tensors).to(device)
    with torch.no_grad():
        features = model.encode_image(image_input)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy()


def extract_clip_embeddings(
    dataframe: pd.DataFrame,
    clip_model_name: str,
    batch_size: int,
) -> tuple[np.ndarray, pd.DataFrame]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    model, preprocess = clip.load(clip_model_name, device=device)
    model.eval()

    embeddings = []
    valid_indices = []
    batch_tensors = []
    batch_indices = []
    start_time = time.time()

    for index, row in dataframe.iterrows():
        tensor = load_image_tensor(Path(row["image_path"]), preprocess)
        if tensor is None:
            continue

        batch_tensors.append(tensor)
        batch_indices.append(index)

        if len(batch_tensors) == batch_size:
            embeddings.append(encode_batch(model, batch_tensors, device))
            valid_indices.extend(batch_indices)
            batch_tensors = []
            batch_indices = []

            if len(valid_indices) % (batch_size * 10) == 0:
                elapsed = time.time() - start_time
                print(f"Embedded {len(valid_indices)} images in {elapsed:.1f}s")

    if batch_tensors:
        embeddings.append(encode_batch(model, batch_tensors, device))
        valid_indices.extend(batch_indices)

    if not embeddings:
        raise RuntimeError("No valid images were embedded.")

    return np.vstack(embeddings), dataframe.loc[valid_indices].reset_index(drop=True)


def split_dataset(embeddings: np.ndarray, dataframe: pd.DataFrame, seed: int):
    labels = dataframe["rebloom_category"].to_numpy()
    train_mask = dataframe["split"].eq("train")
    validation_mask = dataframe["split"].eq("validation")

    if train_mask.any() and validation_mask.any():
        x_train_full = embeddings[train_mask]
        y_train_full = labels[train_mask]
        x_test = embeddings[validation_mask]
        y_test = labels[validation_mask]

        x_train, x_val, y_train, y_val = train_test_split(
            x_train_full,
            y_train_full,
            test_size=0.15,
            random_state=seed,
            stratify=y_train_full,
        )
        return (
            x_train,
            x_val,
            x_test,
            y_train,
            y_val,
            y_test,
            "deepfashion2_train_split_with_validation_as_test",
        )

    x_train, x_temp, y_train, y_temp = train_test_split(
        embeddings,
        labels,
        test_size=0.30,
        random_state=seed,
        stratify=labels,
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.50,
        random_state=seed,
        stratify=y_temp,
    )
    return x_train, x_val, x_test, y_train, y_val, y_test, "stratified_70_15_15"


def build_classifier_candidates(
    model_names: list[str],
    seed: int,
    random_forest_estimators: int,
    mlp_max_iter: int,
) -> dict[str, object]:
    candidates: dict[str, object] = {}

    if "logreg" in model_names:
        candidates["logreg"] = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "logreg",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        solver="lbfgs",
                    ),
                ),
            ]
        )

    if "linear_svm" in model_names:
        candidates["linear_svm"] = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "linear_svm",
                    LinearSVC(
                        class_weight="balanced",
                        max_iter=5000,
                        random_state=seed,
                    ),
                ),
            ]
        )

    if "random_forest" in model_names:
        candidates["random_forest"] = RandomForestClassifier(
            n_estimators=random_forest_estimators,
            class_weight="balanced",
            n_jobs=-1,
            random_state=seed,
        )

    if "mlp" in model_names:
        candidates["mlp"] = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "mlp",
                    MLPClassifier(
                        hidden_layer_sizes=(256, 128),
                        activation="relu",
                        alpha=0.0001,
                        batch_size=256,
                        early_stopping=False,
                        learning_rate_init=0.001,
                        max_iter=mlp_max_iter,
                        n_iter_no_change=10,
                        random_state=seed,
                    ),
                ),
            ]
        )

    return candidates


def evaluate(model, x_values, y_true, labels) -> dict:
    predictions = model.predict(x_values)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        predictions,
        labels=labels,
        average="macro",
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(f1),
        "classification_report": classification_report(
            y_true,
            predictions,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=labels).tolist(),
    }


def flatten_metric_row(model_name: str, training_time: float, val_metrics: dict, test_metrics: dict) -> dict:
    return {
        "model": model_name,
        "training_time_seconds": round(training_time, 3),
        "validation_accuracy": val_metrics["accuracy"],
        "validation_macro_precision": val_metrics["macro_precision"],
        "validation_macro_recall": val_metrics["macro_recall"],
        "validation_macro_f1": val_metrics["macro_f1"],
        "test_accuracy": test_metrics["accuracy"],
        "test_macro_precision": test_metrics["macro_precision"],
        "test_macro_recall": test_metrics["macro_recall"],
        "test_macro_f1": test_metrics["macro_f1"],
    }


def train_and_compare_classifiers(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    label_names: list[str],
    args: argparse.Namespace,
):
    candidates = build_classifier_candidates(
        model_names=args.models,
        seed=args.seed,
        random_forest_estimators=args.random_forest_estimators,
        mlp_max_iter=args.mlp_max_iter,
    )
    if not candidates:
        raise RuntimeError("No classifier candidates selected.")

    comparison_rows = []
    model_metrics = {}
    trained_models = {}

    for model_name, classifier in candidates.items():
        print(f"\nTraining classifier: {model_name}")
        started_at = time.time()
        classifier.fit(x_train, y_train)
        training_time = time.time() - started_at

        val_metrics = evaluate(classifier, x_val, y_val, label_names)
        test_metrics = evaluate(classifier, x_test, y_test, label_names)

        trained_models[model_name] = classifier
        model_metrics[model_name] = {
            "training_time_seconds": training_time,
            "validation": val_metrics,
            "test": test_metrics,
        }
        comparison_rows.append(
            flatten_metric_row(model_name, training_time, val_metrics, test_metrics)
        )

        print(
            f"{model_name}: validation accuracy {val_metrics['accuracy'] * 100:.2f}% "
            f"macro F1 {val_metrics['macro_f1']:.3f} | "
            f"test accuracy {test_metrics['accuracy'] * 100:.2f}% "
            f"macro F1 {test_metrics['macro_f1']:.3f}"
        )

    best_model_name = max(
        comparison_rows,
        key=lambda row: (row["validation_macro_f1"], row["validation_accuracy"]),
    )["model"]
    print(f"\nBest model by validation macro F1: {best_model_name}")

    return (
        best_model_name,
        trained_models[best_model_name],
        model_metrics,
        pd.DataFrame(comparison_rows).sort_values(
            ["validation_macro_f1", "validation_accuracy"],
            ascending=False,
        ),
    )


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    curated = build_curated_dataframe(
        dataset_dir=args.dataset_dir,
        max_samples=args.max_samples,
        max_per_class=args.max_per_class,
        seed=args.seed,
    )
    if curated.empty:
        raise RuntimeError("No DeepFashion2 rows remained after mapping.")

    class_distribution = curated["rebloom_category"].value_counts().sort_index()
    print("Mapped class distribution before embedding:")
    print(class_distribution)

    embeddings, valid_rows = extract_clip_embeddings(
        curated,
        clip_model_name=args.clip_model,
        batch_size=args.batch_size,
    )
    label_names = sorted(valid_rows["rebloom_category"].unique().tolist())
    x_train, x_val, x_test, y_train, y_val, y_test, split_strategy = split_dataset(
        embeddings,
        valid_rows,
        seed=args.seed,
    )

    best_model_name, model, model_metrics, comparison = train_and_compare_classifiers(
        x_train,
        y_train,
        x_val,
        y_val,
        x_test,
        y_test,
        label_names,
        args,
    )
    val_metrics = model_metrics[best_model_name]["validation"]
    test_metrics = model_metrics[best_model_name]["test"]

    artifact = {
        "model": model,
        "model_name": best_model_name,
        "labels": label_names,
        "clip_model": args.clip_model,
        "target_classes": TARGET_CLASSES,
        "category_source": "deepfashion2_clip",
        "split_strategy": split_strategy,
        "train_count": int(len(y_train)),
        "validation_count": int(len(y_val)),
        "test_count": int(len(y_test)),
        "metrics": {
            "validation": val_metrics,
            "test": test_metrics,
            "all_models": model_metrics,
        },
    }

    model_path = args.output_dir / "lens_category_model.joblib"
    metrics_path = args.output_dir / "lens_category_metrics.json"
    comparison_path = args.output_dir / "lens_model_comparison.csv"
    curated_path = args.output_dir / "lens_category_curated_rows.csv"
    distribution_path = args.output_dir / "lens_category_class_distribution.csv"

    joblib.dump(artifact, model_path)
    comparison.to_csv(comparison_path, index=False)
    valid_rows.to_csv(curated_path, index=False)
    valid_rows["rebloom_category"].value_counts().sort_index().to_csv(
        distribution_path,
        header=["count"],
    )

    metrics_payload = {
        "dataset": "DeepFashion2",
        "dataset_dir": str(args.dataset_dir),
        "clip_model": args.clip_model,
        "max_samples": args.max_samples,
        "max_per_class": args.max_per_class,
        "classifier_candidates": args.models,
        "best_model": best_model_name,
        "embedded_image_count": int(len(valid_rows)),
        "split_strategy": split_strategy,
        "train_count": int(len(y_train)),
        "validation_count": int(len(y_val)),
        "test_count": int(len(y_test)),
        "class_distribution": {
            label: int(count)
            for label, count in valid_rows["rebloom_category"]
            .value_counts()
            .sort_index()
            .items()
        },
        "validation": val_metrics,
        "test": test_metrics,
        "all_models": model_metrics,
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    print(f"Saved model: {model_path}")
    print(f"Saved metrics: {metrics_path}")
    print(f"Saved model comparison: {comparison_path}")
    print(f"Best model: {best_model_name}")
    print(
        "Validation accuracy:",
        f"{val_metrics['accuracy'] * 100:.2f}%",
        "macro F1:",
        f"{val_metrics['macro_f1']:.3f}",
    )
    print(
        "Test accuracy:",
        f"{test_metrics['accuracy'] * 100:.2f}%",
        "macro F1:",
        f"{test_metrics['macro_f1']:.3f}",
    )


if __name__ == "__main__":
    main()
