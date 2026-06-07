# ReBloom AI Experiment Notes

These notes summarize the AI experiments used for the report/presentation. The first Polyvore experiments were notebook prototypes; the latest recorded compatibility result is the `clip_10000` experiment suite.

## Compatibility Classifier

- Dataset source: Polyvore outfit compatibility data
- Feature extractor: CLIP ViT-B/32 image embeddings
- Trained model: Random Forest compatibility classifier
- Model purpose: predict whether two fashion items are visually/outfit-compatible
- Current production model file: `ai_service/models/polyvore_compatibility_model.joblib`

## Recorded Notebook Metrics

- Source notebook checked: `C:/Users/SENA REYYAN/Downloads/rebloomai2.ipynb`
- Polyvore metadata items loaded: 251,008
- Compatibility label counts in the full training file: 16,995 compatible + 16,995 incompatible

### Experiment 1: `max_per_class = 1000`

- Balanced outfit subset used: 1,000 compatible outfits + 1,000 incompatible outfits
- Total outfit samples used: 2,000
- Pairwise item samples generated from those outfits: 23,206
- Training samples: 18,564
- Validation samples: 4,642
- Cached unique CLIP embeddings: 9,641
- Validation accuracy: 77.27%
- Validation precision/recall/f1:
  - Incompatible: precision 0.76, recall 0.81, f1-score 0.78
  - Compatible: precision 0.79, recall 0.73, f1-score 0.76

### Experiment 2: `max_per_class = 3000`

- Balanced outfit subset used: 3,000 compatible outfits + 3,000 incompatible outfits
- Total outfit samples used: 6,000
- Validation samples: 13,684
- Validation accuracy: 63.67%
- Validation precision/recall/f1:
  - Incompatible: precision 0.63, recall 0.64, f1-score 0.64
  - Compatible: precision 0.64, recall 0.64, f1-score 0.64
- Confusion matrix:
  - True incompatible predicted incompatible: 4,328
  - True incompatible predicted compatible: 2,471
  - True compatible predicted incompatible: 2,501
  - True compatible predicted compatible: 4,384

### Experiment 3: `max_per_class = 5000`

- Balanced outfit subset used: 5,000 compatible outfits + 5,000 incompatible outfits
- Total outfit samples used: 10,000
- Validation samples: 22,657
- Validation accuracy: 62.13%
- Validation precision/recall/f1:
  - Incompatible: precision 0.62, recall 0.64, f1-score 0.63
  - Compatible: precision 0.63, recall 0.60, f1-score 0.62
- Confusion matrix:
  - True incompatible predicted incompatible: 7,188
  - True incompatible predicted compatible: 4,081
  - True compatible predicted incompatible: 4,499
  - True compatible predicted compatible: 6,889

## Experiment Comparison

| Experiment | Compatible outfits | Incompatible outfits | Validation samples | Accuracy | Compatible precision | Compatible recall | Compatible F1 | Macro F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `max_per_class = 1000` | 1,000 | 1,000 | 4,642 | 77.27% | 0.79 | 0.73 | 0.76 | 0.77 |
| `max_per_class = 3000` | 3,000 | 3,000 | 13,684 | 63.67% | 0.64 | 0.64 | 0.64 | 0.64 |
| `max_per_class = 5000` | 5,000 | 5,000 | 22,657 | 62.13% | 0.63 | 0.60 | 0.62 | 0.62 |

## Updated Polyvore Suite Results

The later Polyvore retraining pipeline used a cleaner category-controlled pair-generation approach and compared multiple classifiers on the same embedding features.

- Dataset source: Polyvore Outfits
- Polyvore split: disjoint
- Metadata items: 251,008
- Total outfits loaded: 70,280
- Selected compatible outfits: 10,000
- Feature extractor: CLIP ViT-B/32
- Pairwise samples generated: 80,736
- Training pair rows: 76,528
- Validation pair rows: 6,996
- Test pair rows: 35,476
- Model selection metric: validation macro F1

### `clip_10000` Classifier Comparison

| Feature extractor | Classifier | Validation accuracy | Validation macro F1 | Validation compatible F1 | Test accuracy | Test macro F1 | Test compatible F1 | Test ROC-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CLIP | Logistic Regression | 65.89% | 0.652 | 0.701 | 67.57% | 0.670 | 0.712 | 0.747 |
| CLIP | Linear SVM | 65.27% | 0.644 | 0.700 | 67.47% | 0.669 | 0.714 | 0.747 |
| CLIP | Random Forest | 56.30% | 0.481 | 0.687 | 57.12% | 0.501 | 0.688 | 0.682 |
| CLIP | MLP | 64.09% | 0.638 | 0.671 | 64.49% | 0.642 | 0.673 | 0.704 |

The best model by validation macro F1 was Logistic Regression on CLIP embeddings. It also achieved the strongest overall test performance with 67.57% test accuracy, 0.670 test macro F1, 0.712 compatible-class F1, and 0.747 ROC-AUC.

### DINOv2 Comparison

We also tested DINOv2 embeddings with 3,000 compatible outfits. The best DINOv2 model was MLP, with 59.82% test accuracy and 0.585 test macro F1. A larger DINOv2 10,000-outfit run failed because the Colab process was killed by the runtime, most likely due to memory limits. Since CLIP 10,000 performed better and the production AI service already uses CLIP embeddings, CLIP remained the preferred feature extractor for integration.

## Model Selection Rationale

Accuracy was not the only selection criterion. We also compared macro F1, compatible-class F1, and ROC-AUC. Macro F1 is important because the model must perform reasonably on both `Compatible` and `Incompatible` classes, while compatible-class F1 is especially relevant for Complete the Look because the application ranks items that should work together in an outfit.

The current best recorded Polyvore experiment is `clip_10000` with Logistic Regression:

- Validation accuracy: 65.89%
- Validation macro F1: 0.652
- Validation compatible F1: 0.701
- Test accuracy: 67.57%
- Test macro F1: 0.670
- Test compatible F1: 0.712
- Test ROC-AUC: 0.747

## Presentation Wording

We retrained the Polyvore compatibility model using CLIP ViT-B/32 image embeddings and a category-controlled pair-generation pipeline. From 70,280 Polyvore outfits and 251,008 metadata items, we selected 10,000 compatible outfits and generated 80,736 balanced pairwise samples. The data was evaluated with separate train, validation, and test pair sets, containing 76,528 training rows, 6,996 validation rows, and 35,476 test rows. We compared Logistic Regression, Linear SVM, Random Forest, and MLP classifiers using validation macro F1 as the selection criterion. Logistic Regression performed best overall, reaching 67.57% test accuracy, 0.670 test macro F1, 0.712 compatible-class F1, and 0.747 ROC-AUC.

## Note

The initial notebook prototype numbers were verified from saved notebook outputs in `rebloomai2.ipynb`. The updated `clip_10000` results were verified from the exported experiment files:

- `rebloom_polyvore_clip_10000.zip`
- `polyvore_suite_summary_all_experiments.zip`
- Structured CSV saved in this repository: `docs/ai_results/polyvore_compatibility_clip_10000_comparison.csv`
