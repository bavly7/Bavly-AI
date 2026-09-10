# Trade-offs

## 1. Per-Class DCGANs vs. Conditional GAN

### Decision: Per-Class DCGANs

**Advantages:**
- ✅ **Label purity guaranteed** — physically impossible to mislabel synthetic images
- ✅ **Easier to debug** — inspect one GAN at a time, isolate failure modes per class
- ✅ **Parallelizable** — train 3 GANs simultaneously on different GPUs
- ✅ **No inter-class confusion** — each GAN only learns one distribution

**Disadvantages:**
- ❌ **3× training time** — must train 3 separate models (450 epochs total vs. 150 for conditional GAN)
- ❌ **No knowledge sharing** — each GAN relearns "skin texture" independently
- ❌ **Higher storage cost** — 3 checkpoints instead of 1

**Why this tradeoff was worth it:**
After CVAE showed overlapping latent space, label purity became the #1 priority. Training time is acceptable (9 hours on Kaggle GPU), and storage cost is negligible (~300MB per checkpoint).

---

## 2. DCGAN vs. StyleGAN / Diffusion Models

### Decision: DCGAN

**Advantages:**
- ✅ **Faster training** — 150 epochs in 2 hours (vs. days for StyleGAN/diffusion)
- ✅ **Simpler architecture** — easier to understand and debug
- ✅ **Works on small datasets** — proven on CIFAR-10, CelebA (thousands of images)
- ✅ **Stable with modern techniques** — Spectral Norm, label smoothing

**Disadvantages:**
- ❌ **Lower image quality** — synthetic lesions look "GAN-ish" (slight checkerboard artifacts)
- ❌ **Limited diversity** — mode collapse on seborrheic keratosis (generated only 2-3 patterns)
- ❌ **Not state-of-the-art** — StyleGAN2/diffusion would produce photorealistic images

**Why this tradeoff was worth it:**
The goal was **not** to generate publication-quality synthetic lesions. The goal was to test whether synthetic augmentation improves F1 scores. DCGAN is sufficient for this experiment, and training time constraints (Kaggle 12-hour limit) make StyleGAN impractical.

**Future work:** A production system would likely use Stable Diffusion or medical-specific generative models (e.g., MedGAN).

---

## 3. 150 Epochs vs. Longer Training

### Decision: 150 Epochs per GAN

**Advantages:**
- ✅ **Fits within Kaggle session limit** — 2 hours per GAN × 3 GANs = 6 hours (leaves 6 hours for classifier training)
- ✅ **Convergence observed** — loss curves plateau around epoch 100-120
- ✅ **Sufficient for proof-of-concept** — F1 improvements were observed despite "GAN-ish" quality

**Disadvantages:**
- ❌ **Seborrheic keratosis mode collapse** — likely needs 300+ epochs to capture intra-class variance
- ❌ **Artifacts visible** — checkerboard patterns, slight color shifts
- ❌ **Lower diversity** — real lesions have more texture variation than synthetic

**Why this tradeoff was worth it:**
The project is a research experiment, not a production tool. 150 epochs was enough to answer the core question: "Does GAN augmentation improve minority-class F1?" (Answer: yes, for 2/3 classes.)

**When this tradeoff is NOT worth it:**
If deploying to a real medical screening system, image quality must be indistinguishable from real lesions → requires StyleGAN2, 1000+ epochs, or domain-expert quality validation.

---

## 4. ResNet18 vs. Deeper Models (ResNet50, EfficientNet)

### Decision: ResNet18

**Advantages:**
- ✅ **Fast training** — converges in 30-50 epochs
- ✅ **Less prone to overfitting** — 11M parameters vs. 25M (ResNet50)
- ✅ **Sufficient capacity** — achieves 0.85+ F1 on majority classes
- ✅ **Pretrained on ImageNet** — transfer learning from natural images

**Disadvantages:**
- ❌ **Lower representational capacity** — deeper models might learn finer lesion features
- ❌ **Potentially lower ceiling** — ResNet50 might achieve 2-3% higher baseline accuracy

**Why this tradeoff was worth it:**
With only 77-142 images per minority class, a deeper model would likely overfit. ResNet18 is the right balance of capacity vs. sample efficiency.

**Evidence:** Validation loss curves showed no overfitting (train/val gap < 5%).

---

## 5. Class-Weighted Loss vs. Focal Loss

### Decision: Class-Weighted Cross-Entropy

**Advantages:**
- ✅ **Simple** — one hyperparameter (weight = 1 / class_count)
- ✅ **Interpretable** — minority classes get higher loss contribution
- ✅ **Works well in practice** — achieved +0.15 F1 on actinic keratosis

**Disadvantages:**
- ❌ **Doesn't focus on hard examples** — treats all minority-class errors equally
- ❌ **Less sophisticated than focal loss** — focal loss down-weights easy examples

**Why this tradeoff was worth it:**
Focal loss introduces two hyperparameters (α, γ) that require tuning. Class weights are deterministic (no tuning needed). Given time constraints, class-weighted loss was sufficient.

**When focal loss would be better:**
If the dataset had "easy" minority-class examples (e.g., obvious actinic keratosis lesions that the model already predicts correctly), focal loss would avoid wasting gradient on them.

---

## 6. Synthetic Images in Validation Set: Yes or No?

### Decision: NO — Validation set is 100% real images

**Advantages:**
- ✅ **Honest evaluation** — metrics reflect performance on real data
- ✅ **Detects overfitting on GAN artifacts** — if train acc >> val acc, model is memorizing synthetic patterns
- ✅ **No leakage** — synthetic images never touch val/test sets

**Disadvantages:**
- ❌ **Lower validation accuracy** — synthetic images are "easier" than real → if included in val, metrics would be artificially inflated
- ❌ **Can't evaluate GAN quality directly** — would need to look at FID, IS, or human evaluation

**Why this tradeoff was worth it:**
The goal is to improve performance **on real test data**, not on synthetic data. Validating on synthetic images would give a false sense of success.

**Alternative approach (not used):**
Split validation into two sets: `val_real` (real images) + `val_synthetic` (synthetic images). Report metrics on both. This adds complexity but provides more insight into GAN quality.

---

## 7. Single Test Evaluation vs. K-Fold Cross-Validation

### Decision: Single 80/20 train/val split, one test evaluation

**Advantages:**
- ✅ **Fast** — train once, evaluate once
- ✅ **No test-set leakage** — test set touched exactly once
- ✅ **Standard practice** — most papers use single train/val/test split

**Disadvantages:**
- ❌ **No confidence intervals** — can't report error bars on F1 scores
- ❌ **Variance due to random seed** — different split (seed=43) might give ±2% F1
- ❌ **Potentially unlucky split** — what if all "hard" examples ended up in test?

**Why this tradeoff was worth it:**
K-fold CV would require training 5 GANs × 5 folds = 25 models (unfeasible on Kaggle). Single split with seed=42 is reproducible and standard for Kaggle competitions.

**Mitigation:**
Inspected class distribution in train/val/test — verified that splits are stratified (proportional class representation).

---

## 8. Modular Code vs. All-in-One Notebook

### Decision: Modular `src/` structure + `full_pipeline.ipynb`

**Advantages:**
- ✅ **Testable** — each module can be unit-tested independently
- ✅ **Reusable** — `dcgan.py` can be imported in other projects
- ✅ **Version control friendly** — Git diffs are meaningful (not giant notebook blobs)
- ✅ **Readable** — clear separation of concerns (data, model, training, evaluation)

**Disadvantages:**
- ❌ **More boilerplate** — need `__init__.py`, imports, etc.
- ❌ **Harder for beginners** — Kaggle users expect all-in-one notebooks
- ❌ **Can't "just run all cells"** — need to understand module structure

**Why this tradeoff was worth it:**
This is a portfolio project demonstrating **software engineering skills**, not a tutorial. Modular code is professional-grade.

**Compromise:**
Kept `full_pipeline.ipynb` as the "entry point" — imports from `src/` but tells the complete story in notebook format.

---

## 9. Honest Reporting vs. Cherry-Picked Results

### Decision: Report all results, including failures

**What I reported:**
- ✅ Seborrheic keratosis showed minimal improvement (+0.02 F1)
- ✅ CVAE failed due to latent space overlap (included t-SNE plot)
- ✅ Original notebook had a label bug (documented in README)
- ✅ GAN samples show visible artifacts (included visual comparison)

**Alternative approach (common in Kaggle):**
- ❌ Only show successful augmentations
- ❌ Hide failed experiments
- ❌ Cherry-pick best epoch/hyperparameters without documenting search process

**Why honest reporting was worth it:**
For a portfolio project, **demonstrating research methodology** (hypothesis → experiment → analysis → pivot) is more valuable than claiming 100% success. Recruiters want to see how you debug failures, not just victories.

---

## Summary: Key Tradeoffs

| Decision | Tradeoff | Worth It? |
|----------|----------|-----------|
| Per-class DCGANs | 3× training time | ✅ Yes (label purity) |
| DCGAN vs. StyleGAN | Lower image quality | ✅ Yes (time constraints) |
| 150 epochs | Artifacts remain | ✅ Yes (proof-of-concept) |
| ResNet18 vs. ResNet50 | Lower capacity | ✅ Yes (avoid overfitting) |
| Class weights vs. focal loss | Less sophisticated | ✅ Yes (simplicity) |
| No synthetic in val | Lower val accuracy | ✅ Yes (honest eval) |
| Single test eval | No confidence intervals | ✅ Yes (feasibility) |
| Modular code | More boilerplate | ✅ Yes (professionalism) |
| Honest reporting | Shows failures | ✅ Yes (research skills) |

**Meta-lesson:** In a 6-week research project, **pick battles carefully**. Perfect image quality is not worth 10× training time if the core hypothesis can be tested with "good enough" synthetic images.
