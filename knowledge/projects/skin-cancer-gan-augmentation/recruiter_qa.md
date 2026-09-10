# Recruiter Q&A

## High-Level Questions

### Q: What is this project in one sentence?
**A:** I tested whether GAN-generated synthetic skin lesion images could improve classifier performance on minority classes in an imbalanced medical imaging dataset — with honest results (worked for 2/3 classes, failed for 1/3).

---

### Q: Why did you build this?
**A:** Three reasons:
1. **Learn generative models** beyond plug-and-play tutorials
2. **Practice research methodology** (hypothesis → experiment → pivot → document)
3. **Demonstrate ML engineering skills** (modular code, reproducible experiments, honest evaluation)

This isn't a "maximized-accuracy-at-all-costs" project — it's a case study in **how to approach an open research question** when you don't know the answer upfront.

---

### Q: What was the result?
**A:** Mixed success:
- **Actinic keratosis:** F1 improved from 0.35 → 0.50 (+43% relative improvement)
- **Dermatofibroma:** F1 improved from 0.42 → 0.58 (+38%)
- **Seborrheic keratosis:** F1 barely changed (0.48 → 0.50, +4%)
- **Majority classes:** Unaffected (no synthetic data leakage)

The README honestly documents what worked and what didn't — including the seborrheic keratosis failure mode (GAN mode collapse due to high intra-class variance).

---

## Technical Deep-Dive Questions

### Q: Why did you pivot from CVAE to DCGAN?
**A:** After training a Conditional VAE, I ran t-SNE on the learned latent space and discovered that minority-class embeddings severely overlapped. This meant the CVAE couldn't distinguish between classes → would generate ambiguous, label-noisy synthetic images.

I showed this visually in the README (t-SNE plot with color-coded classes). The overlap was clear evidence that CVAE wasn't the right tool for this dataset size (~100 images/class).

**Decision:** Pivot to per-class DCGANs — one independent GAN per minority class. This guarantees label purity by construction (each GAN only learns one class).

**Time saved:** ~2 weeks of debugging CVAE hyperparameters that wouldn't have solved the fundamental problem.

---

### Q: How did you debug the label bug?
**A:** Noticed that after adding synthetic data, F1 scores **got worse** on 2 minority classes (actinic keratosis, seborrheic keratosis). This was suspicious — more data should help, not hurt.

**Debugging process:**
1. Manually inspected synthetic images → looked realistic ✅
2. Checked file structure → folders looked correct ✅
3. Printed batch labels during training → all synthetic batches had label=2 (dermatofibroma) ❌

**Root cause:** Original Kaggle notebook hardcoded `label = class_to_idx['dermatofibroma']` for all synthetic images.

**Fix:** Rewrote `SyntheticGANDataset` to read class from parent directory name:
```python
class_name = Path(img_path).parent.name  # e.g., "actinic_keratosis"
label = self.class_to_idx[class_name]
```

**Prevention:** Added assertions to validate label consistency.

---

### Q: Why didn't you use StyleGAN or diffusion models?
**A:** Time and compute constraints.

**StyleGAN2:** Would produce higher-quality images, but requires 1000+ epochs (days of training) and 48GB VRAM (A100 GPU). Kaggle free tier has 16GB VRAM and 12-hour session limit.

**Stable Diffusion:** Even more expensive (requires fine-tuning on ISIC dataset, then 50 denoising steps per image at inference).

**DCGAN:** Converges in 150 epochs (~2 hours), works on 16GB GPU, and produces "good enough" synthetic images to test the core hypothesis: "Does GAN augmentation improve F1?"

**Answer:** Yes, for 2/3 classes. Upgrading to StyleGAN2 might push F1 from 0.50 → 0.55, but that's diminishing returns given the 10× training time increase.

**Trade-off decision:** For a 6-week research project, DCGAN was the right balance of quality vs. feasibility.

---

### Q: How did you ensure no data leakage?
**A:** Strict train/val/test separation:

1. **Split first, then augment:**
   ```
   TRAIN_DIR → random_split(80/20, seed=42)
       ├─ Real_Train (80%) + Synthetic → Training
       └─ Real_Val (20%) → Validation (no synthetic)
   TEST_DIR → Final Evaluation (no synthetic)
   ```

2. **Synthetic images only in training subset** — never touch validation or test sets.

3. **Test set touched exactly once** — all hyperparameter tuning done on validation set.

4. **Added size checks:**
   ```python
   assert len(val_dataset) == len(real_val), "Val set contaminated!"
   ```

**Why this matters:** If synthetic images leak into validation, metrics would be artificially inflated (model overfits on GAN artifacts that don't exist in real test data).

---

### Q: Why per-class GANs instead of a single conditional GAN?
**A:** **Label purity.**

After the CVAE latent-space overlap, I needed to guarantee that synthetic images couldn't be mislabeled. Per-class GANs make this physically impossible:
- DCGAN_A only sees actinic keratosis images
- DCGAN_D only sees dermatofibroma images
- DCGAN_S only sees seborrheic keratosis images

Labels are determined by directory name (not learned):
```
synthetic/
  ├─ actinic_keratosis/  → label = class_to_idx['actinic_keratosis']
  ├─ dermatofibroma/     → label = class_to_idx['dermatofibroma']
  └─ seborrheic_keratosis/ → label = class_to_idx['seborrheic_keratosis']
```

**Trade-off:** 3× training time (must train 3 GANs). But given the label bug experience, correctness > speed.

---

## Behavioral / Soft-Skill Questions

### Q: Tell me about a time when an experiment failed. How did you handle it?
**A:** The CVAE experiment failed (overlapping latent space). Instead of endlessly tuning hyperparameters, I:

1. **Diagnosed the failure mode** — ran t-SNE on latent space, visualized the overlap
2. **Understood the root cause** — 100 images/class is too small for CVAE to learn disentangled representations
3. **Pivoted to a different approach** — per-class DCGANs (simpler, more robust to small data)
4. **Documented the failure** — included t-SNE plot in README with explanation

**Lesson:** Negative results are data. Don't hide failures; use them to inform the next experiment.

**Time saved:** ~2 weeks of debugging a fundamentally broken approach.

---

### Q: How do you prioritize when you have limited time/resources?
**A:** By defining success criteria upfront and focusing on them relentlessly.

**This project's success criteria:**
1. Improve minority-class F1 (primary goal)
2. Don't hurt majority classes (safety check)
3. No test-set leakage (methodological rigor)
4. Document what doesn't work (research honesty)

**What I deprioritized:**
- FID/IS scores (nice-to-have, not blocking)
- StyleGAN2 (10× training time, marginal F1 gain)
- K-fold cross-validation (too expensive, single split is standard)

**Result:** Delivered a complete, honest research project in 6 weeks instead of overextending into "perfect but never finished."

---

### Q: How do you communicate technical work to non-technical stakeholders?
**A:** I wrote the README for two audiences:

**For ML engineers:** Technical details (architecture diagrams, hyperparameters, loss curves).

**For non-technical readers:** High-level story:
1. Problem: Class imbalance hurts minority-class performance
2. Hypothesis: GANs can generate synthetic minority-class images
3. Experiment: Train per-class DCGANs, augment training data
4. Result: Mixed (worked for 2/3 classes)
5. Lesson: Document failures, not just successes

**Visual aids:** Confusion matrices, F1 comparison chart, GAN sample gallery — no ML background needed to understand "baseline vs. augmented."

---

### Q: What would you do differently next time?
**A:** Three things:

1. **Validate data pipeline on day 1** — I lost 3 days debugging the label bug. Should have printed batch labels immediately.

2. **Checkpoint from the start** — Lost 8 hours of GAN training when Kaggle session timed out. Now I checkpoint every 25 epochs by default.

3. **Write README incrementally** — Wrote it at the end, had to recall decisions from 4 weeks ago. Should document design decisions immediately (while reasoning is fresh).

---

## "Why Should We Hire You?" (Portfolio Context)

### Q: What does this project demonstrate about your skills?
**A:** Four things:

1. **Research methodology** — I can form hypotheses, design experiments, analyze results, and pivot when experiments fail.

2. **ML engineering** — Modular code (`src/` structure), reproducible experiments (config.yaml), no test-set leakage, proper validation discipline.

3. **Debugging tenacity** — Found a silent label bug by printing batch labels, diagnosed CVAE failure with t-SNE, debugged GAN mode collapse by inspecting loss curves.

4. **Honest communication** — README documents failures (seborrheic keratosis, CVAE overlap, label bug) alongside successes. This is how real research works.

**Bottom line:** I don't just "run a model and report accuracy." I ask questions, investigate failures, and build systems that are correct, reproducible, and maintainable.

---

### Q: How is this different from a typical Kaggle competition submission?
**A:** Most Kaggle submissions optimize for leaderboard rank. This project optimizes for **learning + demonstrating research skills**.

**Differences:**
- ✅ Documented failed experiments (CVAE, seborrheic keratosis mode collapse)
- ✅ Modular `src/` structure (not a 5000-line notebook)
- ✅ Strict train/val/test discipline (no leakage)
- ✅ Honest reporting (seborrheic keratosis F1 barely improved)
- ✅ Explains *why* design decisions were made (trade-offs section)

**Kaggle submission:** "I got 0.93 accuracy."

**This project:** "I got mixed results (0.50 F1 on 2 classes, 0.02 improvement on 1 class), here's why it failed, here's what I learned, and here's what I'd do differently next time."

**Which demonstrates better engineering skills?** The second one.

---

### Q: What's next for this project?
**A:** If I had 6 more weeks, I'd prioritize:

1. **StyleGAN2** (weeks 1-2) — push minority-class F1 from 0.50 → 0.65
2. **FID/IS metrics** (week 3) — quantify GAN quality objectively
3. **EfficientNet-B3** (week 4) — better baseline classifier
4. **Human evaluation** (weeks 5-6) — can dermatologists distinguish real vs. synthetic?

But for a portfolio project, **knowing when to stop is as important as knowing how to continue**. The current version demonstrates the skills I wanted to show (research methodology, debugging, honest evaluation).

**Production considerations:** If deploying this to a real medical screening system, I'd need:
- Regulatory approval (FDA clearance)
- Dermatologist validation study
- Model uncertainty quantification (confidence calibration)
- Explainability (GradCAM heatmaps showing which lesion regions influenced prediction)

This project is a **research prototype**, not a production medical device.
