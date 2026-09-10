# Key Learnings

## 1. Technical Learnings

### Generative Models Don't Always Work — And That's Fine
**Lesson:** CVAE failed spectacularly (overlapping latent space), but discovering *why* it failed (t-SNE analysis) was more valuable than making it work.

**Application:** In research, negative results are data. Document them, analyze them, and use them to inform the next experiment. The t-SNE plot showing CVAE overlap became one of the most compelling visuals in the project.

**Transferable skill:** Root-cause analysis using visualization tools (t-SNE, UMAP, loss curves).

---

### Small Bugs Can Poison Entire Experiments
**Lesson:** A single-line label bug (all synthetic images → dermatofibroma) silently destroyed 2/3 of minority-class augmentation.

**How I found it:** Printed batch labels during training, noticed all synthetic batches had the same label.

**Prevention:** Always validate labels explicitly when concatenating datasets from different sources.

```python
# Add assertions to dataset __getitem__
assert label in range(num_classes), f"Invalid label {label}"
assert class_name in self.class_to_idx, f"Unknown class {class_name}"
```

**Transferable skill:** Defensive programming — add sanity checks even when "it should work."

---

### Evaluation Discipline Separates Research from Tinkering
**Lesson:** The temptation to "just look at the test set" is real. Resist it.

**Rule I followed:**
1. All hyperparameter tuning on validation set only
2. Test set touched exactly once, at the very end
3. Results reported regardless of outcome (even if disappointing)

**Why it matters:** In production ML, overfitting on "validation" data that's actually being used for tuning is common. Strict train/val/test discipline prevents this.

**Transferable skill:** Research methodology rigor.

---

### GANs Are Sensitive to Hyperparameters (But Not As Much As I Thought)
**Lesson:** Spectral Normalization + label smoothing makes DCGAN surprisingly stable. Didn't need to tune learning rates or architecture much.

**What worked out-of-the-box:**
- DCGAN architecture from original paper
- Adam(lr=0.0002, β₁=0.5)
- Batch size 64
- 150 epochs

**What required tuning:**
- Label smoothing values (settled on 0.9/0.1 after trying 0.8/0.2)
- Spectral Norm placement (discriminator only, not generator)

**Transferable skill:** Start with proven architectures from literature before inventing custom solutions.

---

### Modular Code Is Worth The Boilerplate
**Lesson:** Separating `dataset.py`, `dcgan.py`, `train_generator.py`, `evaluate.py` made debugging 10× easier.

**Example:** When I found the label bug, I only had to fix `SyntheticGANDataset` in `dataset.py` — didn't touch training or evaluation code. If everything was in one notebook, the bug would be duplicated across 5 cells.

**Transferable skill:** Software engineering fundamentals apply to research code.

---

## 2. Domain-Specific Learnings

### Medical Imaging Has Different Constraints Than Natural Images
**Difference:**
- Natural images: maximize perceptual quality (FID, IS, human eval)
- Medical images: **must improve downstream task performance** (F1 on real test data)

**Implication:** A GAN that produces "pretty" synthetic lesions is worthless if it doesn't help the classifier generalize to real test lesions.

**Evidence:** Seborrheic keratosis GANs produced visually decent images but only improved F1 by +0.02 (essentially noise). The synthetic images didn't capture the right intra-class variations.

**Transferable skill:** Define success metrics early, and use them relentlessly. "Looks good" is not a metric.

---

### Class Imbalance Can't Always Be Solved by Data Augmentation
**Lesson:** Two minority classes improved (+0.15, +0.16 F1). One did not (+0.02). No amount of GAN tuning fixed seborrheic keratosis.

**Why:** Seborrheic keratosis has extremely high intra-class variance (lesions vary in color, texture, shape). 77 real images + 1000 synthetic images still don't cover the full distribution.

**Alternative solutions that might work:**
- Few-shot learning (prototypical networks)
- Active learning (collect more real data strategically)
- Multi-task learning (segmentation + classification)

**Transferable skill:** Recognize when a technique has hit its ceiling. Knowing *when to pivot* is as important as knowing *how to implement*.

---

### Transfer Learning from ImageNet Helps — Even for Medical Images
**Lesson:** ResNet18 pretrained on ImageNet (cats, dogs, cars) still learned useful features for skin lesions (edges, textures, color gradients).

**Evidence:** Baseline model achieved 0.85 F1 on majority classes without any medical-specific pretraining.

**Surprise:** I expected medical images to be too different from natural images for transfer learning to work well. I was wrong.

**Transferable skill:** Don't overthink domain gap. Try transfer learning first; custom pretraining is a last resort.

---

## 3. Research Process Learnings

### Pivot Quickly When Experiments Fail
**Timeline:**
- Week 1: Train CVAE
- Week 2: Realize CVAE latent space is garbage (t-SNE), pivot to DCGAN
- Weeks 3-4: Train per-class DCGANs, train classifiers, evaluate

**Counterfactual:** If I had spent weeks 2-4 debugging CVAE hyperparameters, I wouldn't have finished the project.

**Lesson:** Give experiments a fair shot (t-SNE was the diagnostic), but once the failure mode is understood, move on.

**Transferable skill:** Research agility.

---

### Documentation Is Part of The Experiment
**What I documented:**
- t-SNE plot showing CVAE failure
- GAN sample quality (visual comparison of real vs. synthetic)
- Confusion matrices (baseline vs. augmented)
- Per-class F1 comparison chart
- Training curves (loss, accuracy)

**Why it mattered:** When a recruiter asks "why did CVAE fail?" I have a visual answer (t-SNE plot), not a hand-wave.

**Lesson:** Document as you go. Recreating plots 2 weeks later is painful and error-prone.

**Transferable skill:** Research communication.

---

### Honest Reporting Builds Trust
**What I admitted in the README:**
- Seborrheic keratosis showed minimal improvement
- GAN samples have visible artifacts (checkerboard patterns)
- Original notebook had a label bug that I fixed
- No FID/IS scores computed (time constraint)

**Why this matters:** A portfolio project that only shows successes looks like cherry-picked results. A project that documents failures looks like genuine research.

**Recruiter reaction (hypothetical):**
> "You pivoted from CVAE to DCGAN after diagnosing latent space overlap? That's what I want on my team."

**Transferable skill:** Intellectual honesty.

---

## 4. Meta-Learnings (Lessons About Learning)

### I Underestimated The Importance of Data Validation
**Before this project:** "If the code runs without errors, the data must be fine."

**After this project:** "Never trust data until you've visualized it, printed samples, and added assertions."

**New habit:**
```python
# Always print first batch to inspect labels
for imgs, labels in train_loader:
    print(f"Batch labels: {labels.unique()}")
    break
```

---

### I Overestimated The Importance of Model Architecture
**Before this project:** "If I pick the right architecture (StyleGAN vs. DCGAN vs. diffusion), everything will work."

**After this project:** "Architecture matters, but data quality, evaluation discipline, and debugging methodology matter more."

**Evidence:** Fixing the label bug improved F1 by +0.10. Switching from DCGAN to StyleGAN *might* improve F1 by +0.05.

---

### I Learned More from Failures Than Successes
**Successes:**
- Actinic keratosis: +0.15 F1 ✅
- Dermatofibroma: +0.16 F1 ✅

**Failures:**
- Seborrheic keratosis: +0.02 F1 ❌
- CVAE: complete failure ❌

**What I learned from successes:** "GAN augmentation works sometimes."

**What I learned from failures:**
- When CVAEs fail (overlapping latent space)
- When GANs fail (mode collapse on high-variance classes)
- When to pivot (t-SNE diagnostics)
- How to debug label bugs (print batch labels)

**Meta-lesson:** Optimize for learning, not for "impressive results."

---

## 5. Skills I Developed

### Technical Skills
- ✅ GAN training (DCGAN, CVAE)
- ✅ PyTorch dataset pipelines (custom datasets, concatenation, label consistency)
- ✅ Transfer learning (fine-tuning ResNet18)
- ✅ Class imbalance handling (class weights, minority-class augmentation)
- ✅ Research methodology (train/val/test discipline, single test evaluation)
- ✅ Visualization (t-SNE, confusion matrices, training curves)

### Soft Skills
- ✅ Research communication (README that tells a story)
- ✅ Debugging discipline (root-cause analysis, not symptom chasing)
- ✅ Intellectual honesty (documenting failures)
- ✅ Prioritization (150 epochs good enough, StyleGAN not worth the time)

---

## 6. What I Would Do Differently Next Time

### Start with Data Validation, Not Model Training
**What I did:** Trained CVAE for 3 days, then realized data pipeline had a bug.

**What I should have done:** Spend day 1 validating data (print labels, visualize samples, check class distribution).

---

### Implement Checkpointing from Day 1
**What I did:** Lost 8 hours of GAN training when Kaggle session timed out.

**What I should have done:** Checkpoint every 25 epochs from the start.

---

### Write README Incrementally, Not at the End
**What I did:** Wrote README in final 3 days, had to recall decisions from 4 weeks ago.

**What I should have done:** Document design decisions immediately after making them (while reasoning is fresh).

---

## 7. Biggest Surprise

**I expected:** GAN augmentation to either work for all classes or none.

**Reality:** It worked for 2/3 minority classes. The failure case (seborrheic keratosis) taught me that high intra-class variance breaks GANs at small data scales.

**Why this matters:** In production, you can't assume a technique will generalize across all classes. Always evaluate per-class metrics.

---

## One-Sentence Summary

> I learned that debugging methodology, data validation, and honest evaluation discipline matter more than picking the "best" architecture — and that documenting failures is more valuable than hiding them.
