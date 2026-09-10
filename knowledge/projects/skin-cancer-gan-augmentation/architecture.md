# Architecture

## System Overview

```
TRAIN_DIR (ISIC dataset)
    │
    ├─ random_split (80/20, seed=42)
    │   │
    │   ├── Real_Train (80%) ────────────────────────────────────────┐
    │   │                                                             │
    │   │   DCGAN_A (actinic keratosis)  → synthetic/actinic/        │
    │   │   DCGAN_D (dermatofibroma)     → synthetic/dermato/     ───┤ ConcatDataset
    │   │   DCGAN_S (seborrheic kerato.) → synthetic/sebo/           │
    │   │                                                             ▼
    │   │                                                 Augmented ResNet18
    │   │
    │   └── Real_Val (20%) ──► Validation (real images ONLY — no leakage)
    │
TEST_DIR ───────────────────► Final Evaluation (real images ONLY)
```

**Key principle:** Synthetic images only touch the training subset. Validation and test sets remain 100% real images to prevent overfitting on GAN artifacts.

---

## Component Breakdown

### 1. Data Pipeline (`src/dataset.py`)

#### `SkinCancerDataset`
- PyTorch `ImageFolder` wrapper with custom transforms
- Establishes canonical `CLASS_TO_IDX` mapping (critical for label consistency)
- Handles train/val/test splits with stratification

#### `MinorityDataset`
- Filters single class from full dataset
- Used to train per-class DCGANs on minority classes only
- Example: `MinorityDataset(train_ds, class_name='actinic keratosis')`

#### `SyntheticGANDataset`
- Reads generated images from `synthetic/` folders
- **Critical fix:** Reads class label from parent directory name (not hardcoded)
- Maps directory name through canonical `CLASS_TO_IDX`

```python
# WRONG (original notebook — all synthetic images → same label)
label = class_to_idx['dermatofibroma']

# CORRECT (this project)
label = class_to_idx[image_parent_directory_name]
```

#### `AugmentedDataset`
- `ConcatDataset` of real training images + synthetic GAN images
- Used for training augmented ResNet18 classifier

---

### 2. Generative Models

#### CVAE (Conditional Variational Autoencoder) — `src/vae.py`
**Architecture:**
- Encoder: 4 conv layers (3×3 kernels, stride 2) → latent dim 256
- Decoder: 4 transposed conv layers
- Loss: β-VAE (reconstruction + KL divergence, β=1.0)

**Result:** Failed. T-SNE analysis showed minority classes overlap in latent space → blurry, ambiguous reconstructions.

**Why it failed:**
- Small dataset size (77–142 images per class)
- CVAE tries to learn a continuous latent space for ALL classes
- Minority classes don't have enough data to carve out distinct regions

**Decision:** Pivot to per-class DCGANs.

---

#### DCGAN (Deep Convolutional GAN) — `src/dcgan.py`

**Generator:**
```
Input: z ~ N(0, 1), dim=100
    ↓
Linear(100 → 1024×4×4) + BatchNorm + ReLU
    ↓
ConvTranspose2d(1024 → 512, k=4, s=2, p=1) + BatchNorm + ReLU  → 8×8
    ↓
ConvTranspose2d(512 → 256, k=4, s=2, p=1) + BatchNorm + ReLU  → 16×16
    ↓
ConvTranspose2d(256 → 128, k=4, s=2, p=1) + BatchNorm + ReLU  → 32×32
    ↓
ConvTranspose2d(128 → 64, k=4, s=2, p=1) + BatchNorm + ReLU   → 64×64
    ↓
ConvTranspose2d(64 → 3, k=4, s=2, p=1) + Tanh                 → 128×128×3
```

**Discriminator:**
```
Input: 128×128×3 image
    ↓
Conv2d(3 → 64, k=4, s=2, p=1) + LeakyReLU(0.2) + SpectralNorm  → 64×64
    ↓
Conv2d(64 → 128, k=4, s=2, p=1) + BatchNorm + LeakyReLU + SpectralNorm → 32×32
    ↓
Conv2d(128 → 256, k=4, s=2, p=1) + BatchNorm + LeakyReLU + SpectralNorm → 16×16
    ↓
Conv2d(256 → 512, k=4, s=2, p=1) + BatchNorm + LeakyReLU + SpectralNorm → 8×8
    ↓
Conv2d(512 → 1024, k=4, s=2, p=1) + BatchNorm + LeakyReLU + SpectralNorm → 4×4
    ↓
Conv2d(1024 → 1, k=4, s=1, p=0) + Sigmoid                               → 1×1
```

**Training:**
- Loss: Binary cross-entropy (real=1, fake=0)
- Optimizer: Adam (lr=0.0002, β₁=0.5, β₂=0.999)
- Stabilization: Spectral Normalization on discriminator
- Epochs: 150 per class
- Label smoothing: real=0.9, fake=0.1

**Why per-class DCGANs work:**
- Each GAN only learns one class → no inter-class confusion
- Labels are guaranteed correct (directory name = class name)
- Training is parallelizable (3 independent GANs)

---

### 3. Classifier (`src/train_baseline.py`)

**ResNet18:**
- Pretrained on ImageNet (transfer learning)
- Modified final layer: `fc = nn.Linear(512, num_classes=9)`
- Frozen early layers (blocks 1-2), fine-tune blocks 3-4 + fc

**Training:**
- Loss: Cross-entropy with class weights (inverse frequency)
- Optimizer: Adam (lr=0.001)
- Scheduler: ReduceLROnPlateau (patience=5, factor=0.5)
- Early stopping: patience=10 epochs on validation loss
- Full validation loop every epoch (train loss, train acc, val loss, val acc logged)

**Two variants trained:**
1. **Baseline:** Real training data only
2. **Augmented:** Real training data + GAN-generated synthetic images

---

## Data Flow

### Training Phase

```
1. Load ISIC train dataset → random_split(80/20, seed=42)
2. For each minority class:
    a. Extract that class only → MinorityDataset
    b. Train DCGAN for 150 epochs
    c. Generate 500-1000 synthetic images → save to synthetic/<class>/
3. Create AugmentedDataset = Real_Train + Synthetic images
4. Train ResNet18 on AugmentedDataset
5. Validate on Real_Val (no synthetic contamination)
```

### Evaluation Phase

```
1. Load checkpoint (best validation F1)
2. Load TEST_DIR (real images only)
3. Compute per-class precision/recall/F1
4. Generate confusion matrices
5. Compare Baseline vs Augmented F1
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Per-class DCGANs** | Prevents inter-class confusion; guarantees label purity |
| **Spectral Norm on Discriminator** | Stabilizes GAN training; reduces mode collapse |
| **80/20 train/val split** | Standard practice; ensures no test leakage |
| **Synthetic images only in training** | Prevents overfitting on GAN artifacts |
| **Class-weighted loss** | Handles remaining imbalance (even after augmentation) |
| **ImageNet pretrained backbone** | Transfer learning from natural images to medical images |
| **Single canonical CLASS_TO_IDX** | Critical for label consistency across datasets |

---

## Directory Structure

```
skin-cancer-augmentation/
├── src/
│   ├── dataset.py          # All PyTorch Dataset classes
│   ├── vae.py              # CVAE (failed experiment, kept for documentation)
│   ├── dcgan.py            # DCGAN generator + discriminator
│   ├── train_generator.py  # CVAE & DCGAN training loops
│   ├── train_baseline.py   # ResNet18 training (baseline + augmented)
│   └── evaluate.py         # Metrics, confusion matrices, F1 charts
├── notebooks/
│   └── full_pipeline.ipynb # Complete story (EDA → CVAE → DCGAN → evaluation)
├── configs/
│   └── config.yaml         # All hyperparameters in one place
├── assets/                 # Generated plots
└── synthetic/              # GAN-generated images (created during training)
    ├── actinic_keratosis/
    ├── dermatofibroma/
    └── seborrheic_keratosis/
```

---

## Why This Architecture?

**Modularity:** Each component (`dataset.py`, `dcgan.py`, `train_baseline.py`) can be tested independently.

**Reproducibility:** Single `config.yaml` file → all hyperparameters version-controlled.

**Honest evaluation:** No test-set leakage, full validation loop, single test evaluation.

**Research-grade:** Includes failed experiments (CVAE) with explanation, not just cherry-picked successes.
