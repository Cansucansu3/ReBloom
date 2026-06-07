# Lens Category Model Training Plan

This plan describes the supervised AI pipeline for the Lens upload feature.

## Goal

Train a product category classifier that predicts the ReBloom listing category from an uploaded product image.

Target classes:

- `tops`
- `pants`
- `shorts`
- `skirts`
- `dresses`
- `outerwear`

## Dataset

Recommended source: DeepFashion2, a DeepFashion-family dataset with large-scale clothing item annotations.

The SRS describes using a representative DeepFashion subset due to hardware and storage limitations. DeepFashion2 is practical for implementation because it is available through Kaggle and contains approximately 801K annotated clothing items across train/validation/test splits. The Lens category model uses a curated 50,000-sample subset.

Filtering rules:

- Read category labels from DeepFashion2 annotation JSON files.
- If an image contains multiple clothing items, use the largest annotated item as the image-level label.
- Map DeepFashion2 categories into ReBloom clothing classes.
- Keep only rows with valid image files.
- Balance the subset across target classes when possible.
- DeepFashion2 does not include bags or shoes, so those categories stay handled by the CLIP prompt fallback in the AI service.

## Model Pipeline

1. Load DeepFashion2 image files and annotation JSON files.
2. Map each DeepFashion2 clothing category into a ReBloom category.
3. Extract CLIP ViT-B/32 image embeddings.
4. Train and compare supervised classifiers on the frozen CLIP embeddings:
   - Logistic Regression
   - Linear SVM
   - Random Forest
   - MLP Classifier
5. Use DeepFashion2 train images for training/validation and validation images as a held-out test set when available. If not available, use stratified split:
   - 70% train
   - 15% validation
   - 15% test
6. Export:
   - `lens_category_model.joblib`
   - `lens_category_metrics.json`
   - `lens_model_comparison.csv`
   - `lens_category_class_distribution.csv`
   - `lens_category_curated_rows.csv`

## Training Command

Run this in Kaggle/Colab after adding the dataset:

```bash
python ai_service/training/train_lens_deepfashion2_clip_model.py \
  --dataset-dir /kaggle/input/deep-fashion \
  --output-dir /kaggle/working/rebloom_lens_deepfashion2_model \
  --max-samples 50000 \
  --batch-size 64
```

If the dataset is mounted in Kaggle, use the Kaggle dataset folder as `--dataset-dir`:

```bash
python ai_service/training/train_lens_deepfashion2_clip_model.py \
  --dataset-dir /kaggle/input/YOUR_DEEPFASHION2_DATASET_FOLDER \
  --output-dir /kaggle/working/rebloom_lens_deepfashion2_model \
  --max-samples 50000 \
  --batch-size 64
```

## Integration

After training, copy the exported model into:

```text
ai_service/models/lens_category_model.joblib
```

The AI service will automatically use this trained classifier in `/analyze-item` when the model file exists. If the model file is missing, the system falls back to the previous CLIP prompt-based category prediction.

Because DeepFashion2 does not contain bag and shoe labels, the AI service keeps a prompt-based fallback for categories that are not covered by the trained DeepFashion2 classifier.

## Final Training Result

Final experiment:

- Dataset: DeepFashion2
- Feature extractor: CLIP ViT-B/32 frozen image embeddings
- Total curated image count: 49,998
- Class distribution: 8,333 images per class
- Classes: `dresses`, `outerwear`, `pants`, `shorts`, `skirts`, `tops`
- Train count: 36,367
- Validation count: 6,418
- Test count: 7,213

Model comparison:

| Model | Validation Accuracy | Validation Macro F1 | Test Accuracy | Test Macro F1 |
| --- | ---: | ---: | ---: | ---: |
| Logistic Regression | 76.60% | 0.764 | 75.75% | 0.763 |
| Linear SVM | 76.52% | 0.762 | 76.14% | 0.766 |
| Random Forest | 70.77% | 0.705 | 69.55% | 0.698 |
| MLP Classifier | 77.22% | 0.770 | 75.02% | 0.756 |

The final deployed model is the MLP classifier because it achieved the highest validation macro F1-score, which was selected as the model-selection criterion before test evaluation.

## Presentation Wording

We trained a supervised Lens category classifier on a representative 50,000-sample subset of DeepFashion2 using CLIP ViT-B/32 as a frozen feature extractor. DeepFashion2 category annotations were mapped into ReBloom clothing classes, and CLIP embeddings were used as input features. We compared Logistic Regression, Linear SVM, Random Forest, and MLP classifiers on the same embeddings, then selected the final model based on validation macro F1-score. The selected model was evaluated with accuracy, precision, recall, F1-score, and a confusion matrix before integration into the ReBloom AI service.
