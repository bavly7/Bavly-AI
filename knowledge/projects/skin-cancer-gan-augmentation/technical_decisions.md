# Technical Decisions

## 1. Generative Model Architecture: CVAE → DCGAN Pivot

### Initial Choice: Conditional VAE (CVAE)
**Rationale:**
- VAEs are theoretically grounded (variational inference)
- Conditional VAEs can learn class-specific latent representations
- Easier to train than GANs (no adversarial dynamics)

**Implementation:**
- 4-layer convolutional encoder → latent dim 256
- 4-layer deconvolutional decoder
- β-VAE loss: reconstruction + KL divergence (β=1.0)

**Result:** Failed. T-SNE visualization of learned latent space showed severe overlap between minority classes.

**Evidence:**
```
T-SNE of CVAE latent space:
- actinic keratosis (red): cluster overlaps with dermatofibroma
- dermatofibroma (blue): no clear separation
- seborrheic keratosis (green): partially distinct but scattered
```

**Root Cause:** Small dataset size (77-142 images per class) → CVAE cannot learn disentangled representations.

**Consequence:** CVAE generates blurry, ambiguous images that blend features from multiple classes → would introduce label noise if used for augmentation.

**Decision:** Pivot to per-class DCGANs to guarantee label purity by construction.

---

### Final Choice: Per-Class DCGANs

**Why DCGAN:**
- Proven track record on small datasets (CIFAR-10, CelebA)
- Stable training with modern techniques (Spectral Norm, label smoothing)
- Generates sharper images than VAEs (adversarial loss enforces realism)

**Why per-class (not conditional GAN):**
- Conditional GAN still shares a latent space → risk of inter-class confusion
- Per-class GANs physically separate training → impossible to leak labels
- Easier to debug (inspect one GAN at a time)
- Parallelizable training (3 independent GANs)

**Tradeoff:**
- ✅ Label purity guaranteed
- ❌ 3× training time (must train 3 GANs sequentially or parallelize)
- ❌ No shared knowledge between classes (each GAN relearns "skin texture" from scratch)

---

## 2. GAN Stabilization Techniques

### Spectral Normalization on Discriminator
**Why:** Lipschitz constraint prevents discriminator from becoming too strong → generator can still learn.

**Implementation:**
```python
nn.utils.spectral_norm(nn.Conv2d(...))
```

**Alternative considered:** Gradient penalty (WGAN-GP)
- ❌ More complex to implement
- ❌ Slower training (backward pass on interpolated samples)

**Result:** Training converged without mode collapse in 150 epochs.

---

### Label Smoothing
**Why:** Prevents discriminator from over-confident predictions (real=1.0 → real=0.9).

**Implementation:**
```python
real_labels = torch.full((batch_size, 1), 0.9)  # not 1.0
fake_labels = torch.full((batch_size, 1), 0.1)  # not 0.0
```

**Alternative considered:** One-sided label smoothing (smooth only real labels)
- Implemented two-sided for consistency

---

### Progressive Training (Not Used)
**Why not:** DCGAN architecture already scales gradually via transposed convolutions (4×4 → 128×128).

**Tradeoff:**
- ✅ Simpler implementation
- ❌ Slightly less stable than ProGAN-style progressive growing

---

## 3. Data Pipeline Design

### Critical Fix: Label Bug in Original Notebook

**Bug:** All synthetic images assigned to `class_to_idx['dermatofibroma']` regardless of which GAN generated them.

**Impact:** 
- Actinic keratosis synthetic images mislabeled as dermatofibroma
- Seborrheic keratosis synthetic images mislabeled as dermatofibroma
- Model trained on poisoned labels → worse performance

**Fix:** `SyntheticGANDataset` reads parent directory name and maps through canonical `CLASS_TO_IDX`.

```python
# Extract class from directory path
class_name = Path(img_path).parent.name  # e.g., "actinic_keratosis"
label = self.class_to_idx[class_name]
```

**Lesson:** Always validate label consistency when combining multiple data sources.

---

### No Validation/Test Contamination

**Design:**
```
TRAIN_DIR → random_split(80/20, seed=42)
    ├─ Real_Train (80%) + Synthetic → Training
    └─ Real_Val (20%) → Validation (no synthetic)
TEST_DIR → Final Evaluation (no synthetic)
```

**Why:** Synthetic images may contain GAN artifacts (checkerboard patterns, color shifts) that don't exist in real test data → overfitting.

**Alternative considered:** Add synthetic to validation too
- ❌ Would artificially inflate validation metrics
- ❌ No way to detect if model is memorizing GAN artifacts

---

## 4. Classifier Architecture

### ResNet18 (Not ResNet50 or EfficientNet)

**Why ResNet18:**
- ✅ Pretrained on ImageNet → transfer learning
- ✅ Small enough to fine-tune on limited data (150 imgs/class)
- ✅ Fast training (converges in <50 epochs)

**Alternatives considered:**
- ResNet50: ❌ Too many parameters for small dataset → overfitting risk
- EfficientNet-B0: ❌ More complex architecture, longer training time
- Custom CNN from scratch: ❌ No transfer learning → worse performance

**Frozen vs. Fine-Tuned Layers:**
- Frozen: blocks 1-2 (low-level features: edges, textures)
- Fine-tuned: blocks 3-4 + FC layer (high-level features: lesion patterns)

**Why:** Early layers learn generic features (transferable from ImageNet); late layers need domain adaptation (skin lesions ≠ natural images).

---

### Class-Weighted Loss

**Why:** Even after GAN augmentation, some imbalance remains (majority classes still have more real images).

**Implementation:**
```python
class_weights = 1.0 / class_counts  # inverse frequency
criterion = nn.CrossEntropyLoss(weight=class_weights)
```

**Alternative considered:** Focal loss
- ❌ More complex hyperparameter tuning (α, γ)
- ✅ Cross-entropy with class weights is simpler and works well

---

## 5. Evaluation Methodology

### Single Test-Set Evaluation

**Rule:** Test set is touched exactly once, after all hyperparameter tuning on validation set.

**Why:** Prevents information leakage from test set back into training.

**Alternatives rejected:**
- K-fold cross-validation: ❌ Too computationally expensive (would need to train 5 GANs × 5 folds = 15 models)
- Bootstrapped test set: ❌ Complicates reproducibility

---

### Per-Class F1 (Not Overall Accuracy)

**Why:** Accuracy is misleading under class imbalance.

**Example:**
- Baseline model: 92% accuracy, but 0.30 F1 on minority class
- Augmented model: 90% accuracy, but 0.55 F1 on minority class

→ Augmented model is better for the task (detecting rare diseases), despite lower accuracy.

**Metric hierarchy:**
1. Per-class F1 (primary)
2. Confusion matrix (diagnostic)
3. Overall accuracy (reported but not optimized)

---

## 6. Hyperparameters

### GAN Training

| Hyperparameter | Value | Rationale |
|---------------|-------|-----------|
| Latent dim (z) | 100 | Standard DCGAN choice |
| Learning rate | 0.0002 | Standard DCGAN choice |
| β₁ (Adam) | 0.5 | Lower than default (0.9) → less momentum → more stable |
| β₂ (Adam) | 0.999 | Standard |
| Batch size | 64 | Limited by GPU memory (16GB) |
| Epochs | 150 | Convergence observed around epoch 100-120 |
| Label smoothing | 0.9/0.1 | Prevents discriminator overconfidence |

### Classifier Training

| Hyperparameter | Value | Rationale |
|---------------|-------|-----------|
| Learning rate | 0.001 | Standard for fine-tuning |
| Batch size | 32 | Balanced speed vs. stability |
| Optimizer | Adam | Standard choice |
| Scheduler | ReduceLROnPlateau | Adaptive LR based on validation loss |
| Early stopping | patience=10 | Prevents overfitting |

**No grid search:** Would require multiple test-set evaluations → leakage.

---

## 7. Code Architecture

### Modular Structure

**Design:**
```
src/
  ├─ dataset.py       # All PyTorch Dataset classes
  ├─ dcgan.py         # GAN architecture only
  ├─ train_generator.py  # Training loops
  ├─ train_baseline.py   # Classifier training
  └─ evaluate.py      # Metrics, plots
```

**Why:** Each module can be tested independently. Changing GAN architecture doesn't require touching classifier code.

**Alternative considered:** Monolithic Jupyter notebook
- ❌ Hard to test
- ❌ Code duplication
- ❌ No version control on functions

---

### Config File (`configs/config.yaml`)

**Why:** All hyperparameters in one place → reproducibility.

**Alternative considered:** Hardcoded hyperparameters in code
- ❌ Must grep through files to find settings
- ❌ No version control on experiments

---

## 8. Tools & Framework Choices

### PyTorch (Not TensorFlow)

**Why:**
- ✅ More Pythonic (dynamic computation graph)
- ✅ Easier to debug (print statements work naturally)
- ✅ Better GAN ecosystem (most DCGAN tutorials use PyTorch)

### Kaggle Notebooks (Not Local GPU)

**Why:**
- ✅ Free GPU (16GB VRAM)
- ✅ Reproducible environment
- ❌ 12-hour session limit → must checkpoint frequently

---

## Key Takeaways

1. **Pivot quickly when experiments fail** — CVAE didn't work, moved to DCGAN within 24 hours
2. **Per-class models beat conditional models** when classes overlap in latent space
3. **Label bugs are silent killers** — always validate labels across concatenated datasets
4. **Test set is sacred** — touch it exactly once, after all tuning is done
5. **F1 > Accuracy** for imbalanced classification

