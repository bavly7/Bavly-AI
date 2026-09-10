# Problem Statement

## The Core Challenge

**Class imbalance in medical imaging datasets cripples minority-class performance.**

Given:
- ISIC skin cancer dataset with 9 lesion classes
- Severe imbalance (6000:1 ratio between most/least common classes)
- Three minority classes with <150 training images each

**Problem:** A baseline ResNet18 classifier achieves:
- High F1 on majority classes (nevus, melanoma): 0.85–0.92
- Low F1 on minority classes: 0.30–0.50
- Classifier defaults to "predict majority class" for ambiguous cases

## Why This Matters

In medical screening:
- **False negatives on rare diseases are catastrophic** (missed cancer diagnosis)
- High overall accuracy is meaningless if minority classes fail
- Class imbalance is structural (you can't "collect more data" for rare diseases)

## Technical Problem Breakdown

### 1. Data Scarcity
Minority classes have <150 images each:
- actinic keratosis: 77 images
- dermatofibroma: 114 images
- seborrheic keratosis: 142 images

**Consequence:** Model underfits on these classes — not enough training signal.

### 2. Traditional Augmentation Limitations
Standard augmentations (rotation, flipping, color jitter) apply the same transformations to **existing images**:
- ✅ Provides translation/rotation invariance
- ❌ Doesn't create new lesion textures, shapes, or color patterns
- ❌ Can't teach model variations it hasn't seen

### 3. Naive Oversampling Risks
Simply duplicating minority-class images leads to:
- Overfitting (model memorizes exact training examples)
- No new visual patterns learned
- Poor generalization to test set

## The Hypothesis

> Can generative models (GANs) synthesize **realistic, diverse** minority-class images that improve F1 scores without hurting majority-class performance?

## Success Criteria

1. **Improved minority-class F1** (ideally +10% absolute)
2. **No degradation on majority classes** (Δ F1 < 2%)
3. **No test-set leakage** (synthetic data only in training subset)
4. **Reproducible methodology** (seed=42, full validation loop, documented hyperparameters)

## Constraints

- **Limited compute:** Kaggle GPU (16GB), ~12 hours max per experiment
- **No additional data sources:** ISIC dataset only (no external augmentation)
- **Realistic evaluation:** Test set touched exactly once (no hyperparameter tuning on test)
- **Honest reporting:** Document what doesn't work (not just success stories)

## Why Existing Solutions Fall Short

### SMOTE (Synthetic Minority Oversampling)
- Works for tabular data
- ❌ Doesn't understand image structure (produces pixel noise)

### StyleGAN / Diffusion Models
- State-of-the-art image synthesis
- ❌ Requires massive datasets (thousands of images minimum)
- ❌ Computationally expensive (days of training)

### Medical-Specific Augmentation
- Lesion-aware transformations (border expansion, color perturbation)
- ✅ Domain-informed
- ❌ Still constrained to existing image manifold

## The Proposed Solution

**Per-class DCGANs:**
1. Train one independent DCGAN per minority class
2. Generate 500–1000 synthetic images per class
3. Concat with real training data (no validation/test contamination)
4. Train ResNet18 on augmented dataset
5. Compare F1 scores vs. baseline

**Why DCGAN:**
- Proven on small datasets (CelebA, CIFAR-10)
- Stable training with Spectral Normalization
- Fast convergence (150 epochs feasible on Kaggle GPU)
- Easier to debug than VAEs or diffusion models

## What This Project Is NOT Solving

- ❌ Building a production medical diagnostic tool
- ❌ Replacing expert dermatologists
- ❌ Achieving state-of-the-art accuracy on ISIC benchmark
- ❌ Creating photorealistic synthetic lesions indistinguishable from real ones

**This project is:**
✅ A rigorous experiment to test whether GAN-based augmentation helps minority classes
✅ A demonstration of research engineering methodology (pivot, debug, document failures)
✅ A case study in honest ML evaluation (including what didn't work)
