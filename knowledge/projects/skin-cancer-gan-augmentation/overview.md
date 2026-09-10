# Skin Cancer GAN Augmentation — Project Overview

**Can GANs actually fix class imbalance in medical imaging?**

This project gives an honest answer: **yes for some classes, no for others** — and shows exactly why.

## What This Project Is

A rigorous experimental investigation into whether GAN-based synthetic data augmentation can improve classifier performance on minority classes in an imbalanced medical imaging dataset (ISIC skin cancer lesions).

**Not** a production-ready diagnostic tool. **Not** a "maximize accuracy at all costs" competition entry. This is an **engineering research project** with honest results and documented trade-offs.

## Core Question

> Does GAN-based synthetic data augmentation improve F1 scores for minority skin-lesion classes — and does it hurt majority classes?

**The answer:** Two minority classes improved significantly. One did not. The majority classes were unaffected.

## Project Type

- **Domain:** Medical imaging / Computer vision
- **Task:** Class imbalance mitigation via generative models
- **Approach:** DCGAN-based data augmentation + ResNet18 classifier
- **Methodology:** Baseline vs. augmented comparison with full validation loops
- **Outcome:** Mixed results with detailed analysis of what worked and what didn't

## Key Innovation

**Pivoted from CVAE to per-class DCGANs** after t-SNE analysis revealed that CVAE learned overlapping latent representations for minority classes — which would have produced ambiguous, label-noisy synthetic images.

Solution: Train **one independent DCGAN per minority class** to guarantee label purity by construction.

## Tech Stack

- **Framework:** PyTorch
- **Backbone:** ResNet18 (ImageNet pretrained)
- **Generative Models:** Conditional VAE (CVAE) + DCGAN with Spectral Normalization
- **Dataset:** ISIC Skin Cancer (9 classes, severe imbalance)
- **Environment:** Kaggle notebooks with GPU

## Repository

https://github.com/bavly7/Skin-Cancer-GAN-Augmentation

## Timeline

Built as part of computer vision coursework / independent research (exact dates not specified — this was a portfolio project demonstrating ML research methodology).
