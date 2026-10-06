# Challenges & Solutions

## 1. The CVAE Latent Space Overlap Crisis

### Problem
After training a Conditional VAE for 50 epochs, generated images looked blurry and ambiguous — features from multiple classes appeared in single images.

### Investigation
Ran t-SNE on the learned latent space (256-dim → 2D projection):
- Minority classes (actinic keratosis, dermatofibroma, seborrheic keratosis) had severely overlapping clusters
- No clear separation between classes
- Some majority-class samples scattered into minority regions

### Root Cause
**Small dataset size + continuous latent space = insufficient data to learn disentangled representations.**

With only 77-142 images per minority class, the CVAE couldn't carve out distinct regions in 256-dimensional latent space.

### Solution
**Pivot from CVAE to per-class DCGANs:**
- Each DCGAN learns only one class → no inter-class confusion possible
- Physical separation of training data guarantees label purity
- GANs don't require a continuous latent space — they can model discrete modes

### Lesson Learned
> Don't commit to an architecture just because it's "theoretically elegant." If t-SNE/UMAP show your latent space is garbage, pivot immediately.

**Time saved:** 2 weeks of debugging CVAE hyperparameters

---

## 2. The Silent Label Bug

### Problem
After training the augmented ResNet18, F1 scores **got worse** on actinic keratosis and seborrheic keratosis compared to baseline — despite adding 1000 synthetic images per class.

### Investigation
Manually inspected training data:
- Synthetic images looked realistic
- File structure seemed correct (`synthetic/actinic_keratosis/`, `synthetic/dermatofibroma/`, etc.)
- Dataset concatenation logic looked fine

Printed batch labels during training:
```python
print(f"Batch classes: {labels.unique()}")
```
Output: `tensor([2, 2, 2, 2, 2, ...])` ← All dermatofibroma!

### Root Cause
Original Kaggle notebook had this bug:
```python
# WRONG: All synthetic images → dermatofibroma label
label = class_to_idx['dermatofibroma']
```

### Solution
Rewrote `SyntheticGANDataset` to read class from directory name:
```python
class_name = Path(img_path).parent.name  # "actinic_keratosis"
label = self.class_to_idx[class_name]
```

### Verification
Added assertion to dataset:
```python
assert label in range(num_classes), f"Invalid label {label}"
assert class_name in class_to_idx, f"Unknown class {class_name}"
```

### Lesson Learned
> Concatenating datasets from different sources? Validate labels explicitly. Silent label bugs are nearly impossible to detect from accuracy alone.

**Time lost:** 3 days of debugging (retrained model twice before finding bug)

---

## 3. GAN Mode Collapse on Seborrheic Keratosis

### Problem
After 150 epochs, DCGAN for seborrheic keratosis generated only 2-3 distinct image patterns — all synthetic images looked nearly identical.

### Investigation
Inspected discriminator loss:
- Epochs 1-50: D_loss = 0.6-0.8 (normal)
- Epochs 50-100: D_loss = 0.3-0.4 (discriminator winning)
- Epochs 100-150: D_loss = 0.1 (discriminator too strong → generator collapses)

### Root Cause
Seborrheic keratosis images have **high intra-class variance** (lesions vary widely in color, texture, border shape) → discriminator learns to reject "average" synthetic images as "too generic."

### Attempted Solutions

**Attempt 1:** Lower discriminator learning rate
- Set D_lr = 0.0001 (G_lr = 0.0002)
- Result: ❌ Training became unstable (G_loss exploded to 15.0)

**Attempt 2:** Feature matching loss
- Added L2 loss on intermediate discriminator features
- Result: ❌ Slight improvement, but still mode-collapsed after 120 epochs

**Attempt 3:** Increased latent dim (100 → 256)
- Gives generator more capacity to represent variance
- Result: ⚠️ Marginal improvement (3-4 patterns instead of 2-3)

### Final Decision
**Accepted the limitation.** F1 improvement on seborrheic keratosis was minimal (+0.02), documented in README as:

> "Seborrheic keratosis showed minimal improvement — likely needs longer training, a stronger architecture (StyleGAN), or more real data."

### Lesson Learned
> Not all problems have solutions within project constraints. Document failures honestly rather than hiding them.

**Time spent:** 1 week trying different GAN stabilization techniques

---

## 4. Train/Val Split Leakage Risk

### Problem
Initial implementation used `torch.utils.data.random_split()` on the full `TRAIN_DIR` **after** adding synthetic images → some synthetic images ended up in validation set.

### Investigation
Manually inspected validation batch:
```python
for imgs, labels in val_loader:
    print([img.meta['source'] for img in imgs])  # 'real' or 'synthetic'
```
Output: `['real', 'synthetic', 'real', 'synthetic', ...]` ← Contamination!

### Root Cause
Split happened after `ConcatDataset(real_train, synthetic)` → randomization mixed real + synthetic.

### Solution
**Split first, then augment:**
```python
# 1. Split real data only
real_train, real_val = random_split(TRAIN_DIR, [0.8, 0.2], seed=42)

# 2. Add synthetic ONLY to train
train_augmented = ConcatDataset([real_train, synthetic_dataset])

# 3. Validation remains 100% real
val_loader = DataLoader(real_val, ...)
```

### Verification
Added dataset size check:
```python
assert len(val_dataset) == len(real_val), "Val set contaminated!"
```

### Lesson Learned
> Augmentation must happen **after** train/val split, never before. This is obvious in hindsight but easy to miss in code.

**Time lost:** 2 days (had to retrain baseline & augmented models)

---

## 5. Kaggle Session Timeout

### Problem
GAN training takes 150 epochs × 3 classes × 2 hours = **9 hours**. Kaggle notebooks have a 12-hour limit → if I started training too late in the day, the session would timeout before saving checkpoints.

### Solution
**Checkpointing every 25 epochs:**
```python
if epoch % 25 == 0:
    torch.save({
        'epoch': epoch,
        'G_state_dict': generator.state_dict(),
        'D_state_dict': discriminator.state_dict(),
        'G_optimizer': g_optimizer.state_dict(),
        'D_optimizer': d_optimizer.state_dict(),
    }, f'checkpoint_epoch_{epoch}.pth')
```

**Resume training from checkpoint:**
```python
if os.path.exists('checkpoint_epoch_100.pth'):
    checkpoint = torch.load('checkpoint_epoch_100.pth')
    generator.load_state_dict(checkpoint['G_state_dict'])
    # ... load other state
    start_epoch = checkpoint['epoch'] + 1
```

### Lesson Learned
> Cloud notebooks have time limits. Checkpoint frequently or lose hours of GPU time.

**Time saved:** ~8 hours of re-training (happened once before I implemented checkpointing)

---

## 6. Class Imbalance in Confusion Matrix Interpretation

### Problem
Baseline confusion matrix showed:
- Nevus (majority): 600/620 correct
- Actinic keratosis (minority): 8/15 correct

Looking at raw counts, it seemed like the model was "decent" at both.

### Investigation
Computed per-class precision/recall:
- Nevus: F1 = 0.92 (great)
- Actinic keratosis: F1 = 0.35 (terrible)

**Why?** Model predicts "nevus" for ambiguous cases → gets 600/620 nevus correct but misses 7/15 actinic keratosis.

### Solution
**Always report per-class F1, not just accuracy or raw counts.**

Added comparison chart:
```
Class               Baseline F1    Augmented F1    Δ
actinic keratosis      0.35           0.50        +0.15  ✅
dermatofibroma         0.42           0.58        +0.16  ✅
seborrheic keratosis   0.48           0.50        +0.02  ⚠️
nevus                  0.92           0.91        -0.01  ✓
melanoma               0.87           0.88        +0.01  ✓
```

### Lesson Learned
> Accuracy hides class imbalance. Always use F1 (or precision/recall) for imbalanced datasets.

---

## 7. Hyperparameter Tuning Without Test-Set Leakage

### Problem
Wanted to tune GAN learning rates, batch size, number of epochs — but can't use test set for tuning (that's cheating).

### Solution
**Validation set for hyperparameter selection:**
1. Train GAN with different hyperparameters
2. Generate synthetic images
3. Train ResNet18 on augmented data
4. Evaluate on validation set (not test set)
5. Pick hyperparameters that maximize validation F1
6. **One final evaluation on test set** with chosen hyperparameters

**Rule:** Test set is sacred — only one evaluation, after all tuning is done.

### Lesson Learned
> Discipline in evaluation methodology is what separates research from tinkering.

---

## Summary of Hardest Challenges

1. **CVAE latent space overlap** → Pivot to DCGAN ⏱️ 2 weeks
2. **Silent label bug** → 3 days of debugging
3. **GAN mode collapse** → 1 week, accepted limitation
4. **Train/val contamination** → 2 days, retrained models
5. **Kaggle session timeouts** → Implemented checkpointing
6. **Imbalanced evaluation metrics** → Switched to per-class F1
7. **Hyperparameter tuning discipline** → Strict val/test split protocol

**Total debugging time:** ~4 weeks (out of 6-week project)
