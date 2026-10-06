# GitHub Metadata

## Repository Information

**URL:** https://github.com/bavly7/Skin-Cancer-GAN-Augmentation

**Primary Language:** Python

**Framework:** PyTorch

**Dataset:** ISIC Skin Cancer (9 classes, imbalanced)

**License:** Not specified (consider adding MIT or Apache 2.0)

---

## Project Structure

```
skin-cancer-augmentation/
│
├── notebooks/
│   └── full_pipeline.ipynb        # Complete story: EDA → CVAE → DCGAN → evaluation
│
├── src/
│   ├── dataset.py                 # SkinCancerDataset, SyntheticGANDataset, MinorityDataset
│   ├── vae.py                     # ConvCVAE architecture + β-VAE loss
│   ├── dcgan.py                   # DCGANGenerator + DCGANDiscriminator (SpectralNorm)
│   ├── train_generator.py         # CVAE & per-class DCGAN training loops
│   ├── train_baseline.py          # ResNet18 training with full validation loop
│   └── evaluate.py                # Metrics, confusion matrices, F1 charts
│
├── configs/
│   └── config.yaml                # All hyperparameters in one place
│
├── assets/                        # Generated plots (output of notebook)
│   ├── eda_class_distribution.png
│   ├── cvae_loss.png
│   ├── cvae_tsne.png              # Shows latent space overlap → justifies DCGAN pivot
│   ├── gan_samples_actinic_keratosis.png
│   ├── gan_samples_dermatofibroma.png
│   ├── gan_samples_seborrheic_keratosis.png
│   ├── baseline_training_curves.png
│   ├── aug_training_curves.png
│   ├── confusion_matrix_comparison.png  # Baseline vs. Augmented
│   └── f1_comparison.png           # Per-class F1 bar chart
│
├── synthetic/                     # GAN-generated images (created during training)
│   ├── actinic_keratosis/
│   ├── dermatofibroma/
│   └── seborrheic_keratosis/
│
├── requirements.txt               # torch, torchvision, numpy, pandas, matplotlib, seaborn, scikit-learn, PyYAML
│
└── README.md                      # Complete project story (motivation, architecture, results, limitations)
```

---

## Key Files to Review

### 1. `notebooks/full_pipeline.ipynb`
**What it contains:**
- EDA (class distribution, sample images)
- CVAE training + t-SNE latent space visualization
- DCGAN training for 3 minority classes
- Baseline ResNet18 training (real data only)
- Augmented ResNet18 training (real + synthetic)
- Evaluation (confusion matrices, F1 comparison)

**Why review this:** Complete narrative of the project, start to finish.

---

### 2. `src/dataset.py`
**What it contains:**
- `SkinCancerDataset`: PyTorch wrapper around ImageFolder
- `MinorityDataset`: Filters single class for per-class GAN training
- `SyntheticGANDataset`: Reads GAN-generated images with label-from-directory logic (fixes the label bug)

**Why review this:** Shows how I debugged the label bug (reading labels from directory names instead of hardcoding).

---

### 3. `src/dcgan.py`
**What it contains:**
- `DCGANGenerator`: 5-layer transposed conv, batch norm, ReLU/Tanh
- `DCGANDiscriminator`: 5-layer conv, spectral norm, leaky ReLU, sigmoid

**Why review this:** Clean implementation of DCGAN with Spectral Normalization for stability.

---

### 4. `assets/cvae_tsne.png`
**What it contains:**
- t-SNE projection of CVAE latent space
- Color-coded by class (minority classes overlap significantly)

**Why review this:** Visual evidence justifying the pivot from CVAE to DCGAN.

---

### 5. `assets/f1_comparison.png`
**What it contains:**
- Bar chart: Baseline F1 vs. Augmented F1 per class
- Shows which classes improved (+0.15, +0.16) and which didn't (+0.02)

**Why review this:** One-glance summary of results.

---

## README Highlights

### What Makes This README Stand Out

1. **Honest Results Section:**
   > "Two minority classes improved. One did not. Here's why..."

2. **Design Decisions Section:**
   > "Why CVAE → then pivot to GAN?" with t-SNE evidence

3. **Label Bug Documentation:**
   > "The original notebook assigned ALL synthetic images to dermatofibroma. Here's the fix..."

4. **Limitations Section:**
   > "GAN training at 150 epochs produces decent but not photorealistic images. FID score not computed. Seborrheic keratosis mode-collapsed."

### What to Expect
- **Not** a "we achieved 99% accuracy" project
- **Yes** a "here's what worked, what didn't, and what I learned" research case study

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | PyTorch 2.0+ |
| Backbone | ResNet18 (ImageNet pretrained) |
| Generative Models | CVAE (failed), DCGAN (used) |
| Loss | Binary cross-entropy (GAN), cross-entropy with class weights (classifier) |
| Optimizer | Adam (lr=0.0002 for GAN, lr=0.001 for classifier) |
| Stabilization | Spectral Normalization, label smoothing |
| Dataset | ISIC Skin Cancer (9 classes, 10,000+ images) |
| Environment | Kaggle Notebooks (GPU: 16GB VRAM) |

---

## Reproducing Results

### 1. Clone Repository
```bash
git clone https://github.com/bavly7/Skin-Cancer-GAN-Augmentation.git
cd Skin-Cancer-GAN-Augmentation
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Paths
Edit `configs/config.yaml`:
```yaml
paths:
  train_dir: "/path/to/ISIC/train"
  test_dir: "/path/to/ISIC/test"
```

### 4. Run Full Pipeline
Open `notebooks/full_pipeline.ipynb` and run all cells top-to-bottom.

**Expected runtime:**
- CVAE training: 1-2 hours
- DCGAN training (3 classes × 150 epochs): ~6 hours
- Classifier training (baseline + augmented): ~2 hours
- Total: ~10 hours on Kaggle GPU

---

## Citation (If Applicable)

If this project helps your research, consider citing:

```
@misc{bavly2026skincancergan,
  author = {Bavly Waleed},
  title = {Skin Cancer GAN Augmentation: A Research Study on Class Imbalance Mitigation},
  year = {2026},
  howpublished = {\url{https://github.com/bavly7/Skin-Cancer-GAN-Augmentation}},
  note = {Honest evaluation of GAN-based data augmentation for medical imaging}
}
```

---

## Contact

For questions about the project or collaboration opportunities:
- **Email:** bavly.waleed777@gmail.com
- **LinkedIn:** https://www.linkedin.com/in/bavly-waleed
- **GitHub:** https://github.com/bavly7

---

## License

**Recommended:** Add MIT or Apache 2.0 license to repository.

**Why:** Makes it clear that others can use/modify the code for learning purposes.

**Note:** If using ISIC dataset, comply with their usage terms (non-commercial research only).
