
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
