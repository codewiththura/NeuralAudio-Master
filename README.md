
# Audio Processing Toolkit

A professional suite of Python automation Neural Network Processing (NNP) tools designed for batch processing audio files. This toolkit provides studio-quality noise reduction and broadcast-standard loudness normalization for content creators, podcasters, and video editors.

## Included Tools

### 1. Audio Enhancer (`audio_enhancer.py`)
A complete "one-click" mastering solution. It performs three critical steps on every file:
1.  **Standardization:** Converts inputs to a high-fidelity WAV format.
2.  **Loudness Normalization:** Adjusts volume to a target level (default: -23 LUFS) to ensure consistent audio levels.
3.  **Advanced Denoising:** Removes background noise (hiss, hum, static) using neural network processing while preserving voice clarity.
4.  **Final Export:** Delivers a polished, high-quality MP3 (320kbps).

### 2. Audio Normalizer (`audio_normalizer.py`)
A dedicated utility for strict loudness compliance without altering the sound character.
* **Best for:** Clean recordings that only need volume leveling.
* **Output:** High-quality WAV files normalized to specific LUFS targets (configurable).

---

## Features
* **Batch Processing:** Process entire folders of audio files at once.
* **Drag & Drop Support:** Simply drag a file or folder into the terminal window when prompted.
* **Smart Cleanup:** Automatically removes temporary cache files after processing.
* **Format Support:** Handles `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.aac`, and more.

---

## Installation

### Prerequisites
1.  **Python 3.8+** installed on your system.
2.  **FFmpeg** installed and added to your system PATH (required for format conversion).

### Setup
1.  Clone this repository or download the scripts.
2.  Install the required dependencies using the requirements file.

Note: If you encounter installation errors on Windows, ensure you have the Microsoft C++ Build Tools installed.)

    pip install -r requirements.txt

## Usage

### Running the Audio Enhancer

This is the main tool for cleaning up noisy recordings.

    python audio_enhancer.py

 1. Run the script.
 2. Paste a file path, folder path, or drag-and-drop your audio source.
 3. The script will generate a `Mastered_Audio_Output` folder with your cleaned files.

### Running the Normalizer

Use this if you only need to standardize volume levels.

    python audio_normalizer.py

 1. Run the script.
 2. Select your source files.
 3. The script will generate a `Normalized_Audio_Output` folder.

## Configuration

You can adjust the target loudness in the script configuration section at the top of either file:

    Target loudness level (Broadcast standard: -23, Web/Podcast: -16)
    TARGET_LOUDNESS = -23

## Troubleshooting Installation Errors

If you encounter errors during installation mentioned "Rust", "Cargo", or "Microsoft Visual C++ 14.0", this is a common issue on Windows when using very new versions of Python (like 3.12).

### The Problem
Some deep learning libraries may not yet have pre-built files ("wheels") for the absolute latest Python version. When this happens, `pip` tries to compile the code from scratch, which fails if you don't have C++ and Rust compilers installed.

### The Easy Fix: Use Python 3.10
Instead of installing 4GB+ of C++ build tools, the simplest solution is to use **Python 3.10**. The libraries are already pre-compiled for this version, so they install instantly.

**Steps to fix:**

1.  **Install Python 3.10:**
    Download it from the [official Python website](https://www.python.org/downloads/release/python-31011/) (ensure you grab the Windows installer).

2.  **Create a specific Virtual Environment:**
    Delete your old `venv` folder, then run this command to force a Python 3.10 environment:
    ```bash
    py -3.10 -m venv venv
    ```

3.  **Activate & Install:**
    ```bash
    venv\Scripts\activate
    pip install -r requirements.txt
    ```

This method bypasses the need for "Microsoft Visual C++ Build Tools" entirely.