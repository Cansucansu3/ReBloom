# Polyvore Compatibility Retraining Plan

This note describes the improved Complete the Look training pipeline.

## Goal

Train a stronger compatibility classifier for outfit recommendation. The model
predicts whether two fashion items can work together in the same outfit.

The production endpoint that uses this model is:

```text
POST /outfit-rank
```

Backend usage:

```text
backend/app/routers/recommendations.py
```

AI service usage:

```text
ai_service/services/compatibility_service.py
```

## Dataset Used

We use the Hugging Face dataset:

```text
mvasil/polyvore-outfits
```

This is the same Polyvore Outfits dataset family used in the previous notebook.
It contains curated outfits, item metadata, product images, and compatibility
split files.

Important files:

- `polyvore_item_metadata.json`
  - item metadata such as title, description, category id, and semantic category
- `disjoint/train.json`, `disjoint/valid.json`, `disjoint/test.json`
  - outfit definitions that map outfit items to real item ids
- `disjoint/compatibility_train.txt`
  - compatibility labels for outfit samples
- `data/disjoint/train.parquet`
  - product image bytes for items
- `data/disjoint/valid.parquet`
  - validation item images
- `data/disjoint/test.parquet`
  - test item images

We use the `disjoint` split by default because it is harder and more realistic:
items in the test split should not overlap with training items.

## Current Problem

The previous Polyvore experiments converted outfit-level labels directly into
all possible item pairs. This can create noisy labels because an incompatible
outfit may still contain some compatible item pairs.

For example, an outfit can be labeled incompatible overall, but its shirt and
jeans may still match. If that pair is labeled incompatible, the model receives
conflicting supervision.

## Improved Pair Generation

The new training script uses:

- Positive pairs: complementary items from the same compatible outfit.
- Negative pairs: complementary-category items sampled from different outfits.
- Outfit-level split: outfits are split before pair generation, reducing train
  and test leakage.
- Category control: pairs are generated only between outfit-relevant categories
  such as top-pants, skirt-shoes, dress-bag, and outerwear-top.

Training script:

```text
ai_service/training/train_polyvore_compatibility_model.py
```

## Detailed Training Pipeline

### 1. Download Dataset

In Colab, the dataset is downloaded from Hugging Face:

```python
from huggingface_hub import notebook_login, snapshot_download

notebook_login()

base_dir = snapshot_download(
    repo_id="mvasil/polyvore-outfits",
    repo_type="dataset",
    local_dir="/content/polyvore-outfits"
)
```

The script receives this folder through:

```text
--dataset-dir /content/polyvore-outfits
```

### 2. Read Outfit Compatibility Labels

The compatibility files contain lines similar to:

```text
1 12345_1 12345_2 12345_3
0 45678_1 45678_2 45678_3
```

The first value is the label:

- `1`: compatible outfit
- `0`: incompatible outfit

The remaining values are outfit tokens, not direct item ids. Therefore, the
script first reads `disjoint/train.json`, `valid.json`, and `test.json` to build
a token mapping:

```text
set_id + item index -> item_id
```

Example:

```text
12345_2 -> 193587212
```

This step is important because the parquet image table is indexed by real
`item_id`, not by the outfit token.

### 3. Map Polyvore Categories To ReBloom Categories

Each item is matched with metadata from `polyvore_item_metadata.json`.

The main field used for category mapping is:

```text
semantic_category
```

Polyvore categories are mapped into ReBloom categories:

- `tops`
- `pants`
- `shorts`
- `skirts`
- `dresses`
- `outerwear`
- `shoes`
- `bags`

Items that cannot be mapped to one of these categories are skipped.

### 4. Split At Outfit Level

The improved script avoids pair-level leakage. Instead of creating all pairs
first and then splitting them, it splits outfits first:

```text
outfits -> train / validation / test
```

Then pair generation happens separately inside each split.

This matters because if pairs from the same outfit appear in both train and
validation, the model may memorize outfit-specific visual cues and validation
performance becomes too optimistic.

### 5. Generate Positive Pairs

Positive pairs are created from compatible outfits.

For each compatible outfit, the script forms item pairs only when their
categories are complementary.

Examples:

- top + pants
- top + skirt
- dress + shoes
- dress + bag
- skirt + shoes
- outerwear + top

This avoids weak pairs such as top + top or shoes + shoes, which are not useful
for Complete the Look.

### 6. Generate Negative Pairs

Negative pairs are generated from different outfits while preserving category
logic.

For example:

```text
top from outfit A + pants from outfit B -> negative pair
```

This is better than using all pairs from an incompatible outfit because some
items inside an incompatible outfit may still match each other.

The goal is to reduce label noise.

### 7. Load Product Images From Parquet

In this Hugging Face dataset, images are not stored as ordinary `.jpg` files.
They are stored inside parquet rows as bytes:

```python
row["image"]["bytes"]
```

The script reads only the item images needed by the selected outfits, converts
the bytes into PIL images, and passes them to the feature extractor.

### 8. Extract Visual Embeddings

Default production-compatible option:

```text
CLIP ViT-B/32
```

CLIP is used as a frozen feature extractor:

- CLIP weights are not trained.
- Each item image is converted into a normalized embedding vector.
- The classifier learns on top of those embeddings.

Optional comparison:

```text
DINOv2
```

DINOv2 can be used for a second experiment, but a DINOv2 compatibility model
cannot replace the current production model until the AI service also supports
DINOv2 embeddings.

### 9. Build Pair Features

For each item pair, we combine the two image embeddings into one feature vector:

```text
left_embedding
right_embedding
abs(left_embedding - right_embedding)
left_embedding * right_embedding
```

This is the same feature idea used by the current production compatibility
service.

Intuition:

- `left_embedding` and `right_embedding`: individual item appearance
- `abs difference`: how visually different the two items are
- `elementwise product`: how strongly the visual dimensions align

### 10. Train Multiple Classifiers

The script compares:

- Logistic Regression
- Linear SVM with probability calibration
- Random Forest
- MLP Classifier

All models use the same pair features, so the comparison is fair.

### 11. Evaluate The Models

Metrics saved:

- accuracy
- macro precision
- macro recall
- macro F1
- compatible-class precision
- compatible-class recall
- compatible-class F1
- ROC-AUC
- confusion matrix

For Complete the Look, compatible-class metrics matter because the application
uses the model to rank items that should go well together.

### 12. Select And Export The Best Model

By default, the best model is selected using:

```text
validation_macro_f1
```

Alternative:

```text
validation_compatible_f1
```

This may be more useful if we want to optimize specifically for finding good
compatible recommendations.

The exported model is:

```text
polyvore_compatibility_model.joblib
```

If the selected model uses CLIP embeddings, it can be copied into:

```text
ai_service/models/polyvore_compatibility_model.joblib
```

after we confirm that it performs better than the existing model.

## Models To Compare

The script compares:

- Logistic Regression
- Linear SVM with probability calibration
- Random Forest
- MLP Classifier

Metrics:

- Accuracy
- Macro precision
- Macro recall
- Macro F1
- Compatible-class precision/recall/F1
- ROC-AUC
- Confusion matrix

## Feature Extractors

### CLIP

Default and production-compatible option:

```text
--feature-extractor clip
```

This uses CLIP ViT-B/32 image embeddings. The current AI service already uses
CLIP embeddings, so a CLIP-trained artifact can replace the production
compatibility model after evaluation.

### DINOv2

Comparison option:

```text
--feature-extractor dinov2
```

DINOv2 is image-only and can be useful for shape, texture, and visual retrieval
features. A DINOv2-trained artifact is useful for experiments, but it requires
AI service embedding support before deployment.

## Example Commands

### Colab Setup

```bash
!pip install -q pandas pyarrow joblib scikit-learn git+https://github.com/openai/CLIP.git
```

Then write the training script into Colab:

```python
%%writefile train_polyvore_compatibility_model.py
# paste ai_service/training/train_polyvore_compatibility_model.py here
```

### Small Smoke Test

Run this first to verify that the dataset format is read correctly:

```bash
!python train_polyvore_compatibility_model.py \
  --dataset-dir /content/polyvore-outfits \
  --output-dir /content/rebloom_polyvore_clip_test \
  --data-format hf_parquet \
  --polyvore-split disjoint \
  --max-positive-outfits 1000 \
  --feature-extractor clip \
  --models logreg random_forest \
  --batch-size 64
```

### CLIP Experiment

```bash
!python train_polyvore_compatibility_model.py \
  --dataset-dir /content/polyvore-outfits \
  --output-dir /content/rebloom_polyvore_clip_10000 \
  --data-format hf_parquet \
  --polyvore-split disjoint \
  --max-positive-outfits 10000 \
  --feature-extractor clip \
  --models logreg linear_svm random_forest mlp
```

### DINOv2 Experiment

```bash
!pip install -q transformers

!python train_polyvore_compatibility_model.py \
  --dataset-dir /content/polyvore-outfits \
  --output-dir /content/rebloom_polyvore_dinov2_10000 \
  --data-format hf_parquet \
  --polyvore-split disjoint \
  --max-positive-outfits 10000 \
  --feature-extractor dinov2 \
  --models logreg linear_svm random_forest mlp
```

### Larger Experiment

```bash
!python train_polyvore_compatibility_model.py \
  --dataset-dir /content/polyvore-outfits \
  --output-dir /content/rebloom_polyvore_clip_15000 \
  --data-format hf_parquet \
  --polyvore-split disjoint \
  --max-positive-outfits 15000 \
  --feature-extractor clip \
  --selection-metric validation_compatible_f1
```

## Outputs

The script exports:

- `polyvore_compatibility_model.joblib`
- `polyvore_metrics.json`
- `polyvore_model_comparison.csv`
- `polyvore_pairs.csv`
- `polyvore_train_pairs_used.csv`
- `polyvore_validation_pairs_used.csv`
- `polyvore_test_pairs_used.csv`

Only the final model and metrics/comparison files should be copied into the
project. The generated pair CSV files can be kept outside Git if they become too
large.

## Presentation Wording

We retrained the Polyvore compatibility model using a category-controlled
pair-generation strategy. Instead of assigning outfit-level labels directly to
every possible item pair, we created positive pairs from compatible outfits and
negative pairs from different outfits while preserving complementary category
relationships. We split the data at the outfit level before pair generation to
reduce leakage, compared Logistic Regression, Linear SVM, Random Forest, and MLP
classifiers, and selected the final model using validation F1-based metrics.
