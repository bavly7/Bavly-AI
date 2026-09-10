# Motivation — Why This Project?

## The Real-World Problem

Medical imaging datasets suffer from severe class imbalance:
- Common conditions: thousands of labeled examples
- Rare diseases: tens to hundreds of examples

**Example from ISIC skin cancer dataset:**
- Nevus (common benign moles): ~6,000 images
- Dermatofibroma (rare benign tumor): **~114 images**
- Actinic keratosis (precancerous): **~77 images**

Traditional data augmentation (rotation, flipping, color jitter) doesn't create **new visual patterns** — it just transforms existing images.

## The Hypothesis

> Can generative models (GANs) synthesize realistic minority-class images that improve classifier performance without hurting majority classes?

This is not obvious! Synthetic data could:
- ✅ Teach the model new intra-class variations
- ❌ Introduce unrealistic artifacts that confuse the model
- ❌ Create "easier" synthetic examples that don't transfer to real test images

## Why I Built This

Three reasons:

### 1. Personal Challenge
I wanted to move beyond "plug-and-play" Kaggle competition code and understand the **engineering decisions** behind generative models in production ML systems:
- When does a CVAE fail? (Answer: when minority classes overlap in latent space)
- How do you debug GAN training? (Answer: visual inspection + loss curves + t-SNE)
- What's the right way to evaluate synthetic data? (Answer: measure downstream task performance, not just perceptual quality)

### 2. Honest Experimentation
Most GAN tutorials show cherry-picked success cases. I wanted to **document the failures** too:
- Seborrheic keratosis showed minimal F1 improvement despite 150 GAN epochs
- CVAE produced blurry, ambiguous images (documented with t-SNE evidence)
- Original notebook had a silent label bug that poisoned 2/3 minority classes

This project is as much about **what didn't work** as what did.

### 3. Portfolio Differentiation
Anyone can fine-tune a ResNet. Showing that I can:
- Diagnose generative model failures (CVAE overlap)
- Pivot architecture based on evidence (CVAE → DCGAN)
- Write production-grade code (modular `src/` structure, config files, no leakage)
- Communicate tradeoffs honestly (README acknowledges limitations)

...demonstrates **research engineering** skills, not just model training.

## Why GANs (Not Diffusion Models)?

In 2024–2026, diffusion models dominate image synthesis. But:
- DCGAN is **simpler to debug** (discriminator loss tells you if it's learning)
- Faster to train (150 epochs vs. thousands of denoising steps)
- Easier to understand failure modes (mode collapse is visually obvious)

For a **learning project** on a class imbalance problem, DCGAN was the right pedagogical choice. A production system might use stable diffusion or medical-specific generative models.

## What Success Looks Like

**Not** "100% accuracy on skin cancer."

**Success** means:
1. F1 scores improve for at least one minority class
2. Majority classes are unaffected (no synthetic data leakage)
3. The methodology is reproducible (seed=42, full validation loop, single test evaluation)
4. Failures are documented and explained (seborrheic keratosis, CVAE overlap)

This project achieved all four.
