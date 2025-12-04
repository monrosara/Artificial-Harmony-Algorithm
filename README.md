---
title: "Artificial Harmony Algorithm"
emoji: "🎵"
sdk: "docker"
license: "MIT"
short_description: "Generate AI-powered harmonic music mixes from audio samples."
---

# 🎵  Artificial Harmony Algorithm

[![Hugging Face Spaces](https://img.shields.io/badge/🤗-Hugging%20Face%20Space-blue)](https://huggingface.co/spaces/Dmtlant/aha-algorithm)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/monrosara/Artificial-Harmony-Algorithm)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent music mixer that creates harmonious, multi-layer compositions from audio samples using machine learning and the Camelot Wheel System.

## ✨ Features

- 🎚️ **Multi-layer composition** (1-8 layers simultaneously)
- 🎹 **Harmonic mixing** with Camelot Wheel System
- ⚡ **BPM synchronization** and tempo matching
- 📤 **Sample upload support** (WAV, MP3, FLAC, AIFF, ZIP)
- 🧪 **Experimental mode** for unique combinations
- 🔄 **Real-time generation** with progress tracking
- 💾 **Mix export** in WAV format
- 🐳 **Docker support** for easy deployment
- 🌐 **Web interface** built with Gradio

## 🌐 Live Demo

Try the live version on Hugging Face Spaces:  
**[https://huggingface.co/spaces/Dmtlant/aha-algorithm](https://huggingface.co/spaces/Dmtlant/aha-algorithm)**

> ⚠️ **Note:** The demo may take 30-60 seconds to load on first access due to server startup.

## 🚀 Quick Start

### Option 1: Online Demo (Recommended)

1. Visit **[https://huggingface.co/spaces/Dmtlant/aha-algorithm](https://huggingface.co/spaces/Dmtlant/aha-algorithm)**
2. Wait for the interface to load
3. Start creating mixes immediately

### Option 2: Local Installation

**Prerequisites:**
- Python 3.10+
- Git
- FFmpeg (for audio processing)
- Libraries: gradio, librosa, numpy, scipy, pydub, soundfile

```bash
# Clone the repository
git clone https://github.com/monrosara/Artificial-Harmony-Algorithm
cd Artificial-Harmony-Algorithm

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

Access at: http://localhost:7860
