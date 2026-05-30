# ReBloom AI Experiment Notes

These notes summarize the CLIP + compatibility classifier experiment used for the report/presentation.

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

## Model Selection Rationale

Accuracy was not the only selection criterion. We also compared precision, recall, and F1-score, especially for the `Compatible` class because the application uses this model to rank compatible outfit recommendations in Complete the Look.

The `max_per_class = 1000` model performed best across all recorded metrics:

- Highest validation accuracy: 77.27%
- Highest Compatible precision: 0.79
- Highest Compatible recall: 0.73
- Highest Compatible F1-score: 0.76
- Highest macro F1-score: 0.77

The larger 3,000/class and 5,000/class experiments introduced more data diversity, but their validation performance decreased. This does not automatically mean that the larger datasets are useless; the task may become harder because outfit-level labels are converted into pairwise item labels. In an incompatible outfit, some item pairs can still be visually compatible, which can introduce label noise. For the current demo and evaluation setup, the 1,000/class model is the best-performing and most stable choice.

## Presentation Wording

We used CLIP ViT-B/32 as a feature extractor and trained a Random Forest compatibility classifier on a balanced Polyvore subset. The full compatibility training file contained 16,995 compatible and 16,995 incompatible outfit labels. In our best experiment, we sampled 1,000 compatible and 1,000 incompatible outfits, which produced 23,206 pairwise item samples and reached 77.27% validation accuracy. We also tested larger subsets with 3,000 and 5,000 samples per class; however, performance decreased to 63.67% and 62.13% accuracy. We selected the 1,000/class model because it performed best not only in accuracy, but also in Compatible-class precision, recall, and F1-score, which are important for the recommendation feature.

## Note

These numbers were verified from the saved notebook outputs in `rebloomai2.ipynb`.
