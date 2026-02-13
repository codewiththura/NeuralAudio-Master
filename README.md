
# Audio Processing Toolkit

A professional suite of Python automation Neural Network Processing (NNP) tools designed for batch processing audio files. This toolkit provides studio-quality noise reduction and broadcast-standard loudness normalization for content creators, podcasters, and video editors.

## Key Features

* **Standalone Operation:** Powered by `PyAV`. No need to install FFmpeg or configure system PATH variables.
* **AI Denoising:** Uses Neural Network to remove background noise while preserving voice quality.
* **Loudness Compliance:** strictly adheres to broadcast standards (EBU R128, AES) with selectable presets.
* **Batch Workflow:** Process entire folders at once with drag-and-drop support.
* **Continuous Processing:** Tools run in a loop, allowing you to process multiple batches without restarting.

---

## Included Tools

### 1. Audio Enhancer (`audio_enhancer.py`)
A complete "one-click" mastering solution. Best for raw recordings that need cleanup.

**Workflow:**
1.  **Standardization:** Converts inputs to a high-fidelity WAV format.
2.  **Loudness Normalization:** Adjusts volume to a target level (default: -23 LUFS) to ensure consistent audio levels.
3.  **Advanced AI Denoising:** Removes background noise (hiss, hum, static) using advanced neural network processing while preserving voice clarity.
4.  **Final Export:** Delivers a polished, high-quality MP3 (320kbps).

### 2. Audio Normalizer (`audio_normalizer.py`)
A dedicated utility for strict loudness compliance without altering the sound character.

**Workflow:**
* **Selectable Targets:** Choose from TV (-23 LUFS), Podcast (-16 LUFS), Streaming (-14 LUFS), or Custom.
* **Non-Destructive:** Only adjusts gain; does not apply EQ or compression.
* **Output:** High-Quality WAV files ready for final delivery.

---

## Installation

### Prerequisites
* **Python 3.10** (Recommended to avoid compilation errors).
* *Note: Python 3.11+ may require Microsoft C++ Build Tools for some audio libraries.*

### Step-by-Step Setup

1.  **Clone the Repository**
    Download this folder to your local machine.

2.  **Set up a Virtual Environment (Recommended)**
    Open your terminal in the project folder and run:
    ```bash
    # Windows
    py -3.10 -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3.10 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage Guide

### Using the Audio Enhancer

1.  **Launch the tool:**
    ```bash
    python audio_enhancer.py
    ```
2.  **Select Input:**
    Drag and drop a file or a folder containing audio files into the terminal window and press **Enter**.
3.  **Processing:**
    The script will automatically convert, normalize, and denoise each file.
4.  **Result:**
    Find your mastered files in the `Mastered_Audio_Output` folder.

### Using the Audio Normalizer

1.  **Launch the tool:**
    ```bash
    python audio_normalizer.py
    ```
2.  **Select Target Loudness:**
    A menu will appear asking for your desired standard:
    * `1` TV / Broadcast (-23 LUFS)
    * `2` Podcast / Mobile (-16 LUFS)
    * `3` Music Streaming (-14 LUFS)
    * `4` Custom Value
3.  **Select Input:**
    Drag and drop your source files or folder.
4.  **Processing:**
    The script analyzes the loudness of each file and adjusts it to match your target.
5.  **Finish or Continue:**
    Once the batch is done, you can choose to start a new batch with different settings or exit.

---

### Troubleshooting Installation

If you encounter errors during installation mentioning **"Rust"**, **"Cargo"**, or **"Microsoft Visual C++ 14.0"**, this is a common issue when using very new versions of Python (like 3.12+).

### The Easy Fix: Use Python 3.10
Instead of installing heavy build tools, the simplest solution is to use **Python 3.10**. The libraries used in this project are pre-compiled for this version, so they install instantly.

**Steps to fix:**
1.  **Install Python 3.10:** Download it from the [official Python website](https://www.python.org/downloads/).
2.  **Recreate Environment:** Delete your old `venv` folder and create a new one using the command: `py -3.10 -m venv venv`.

*(Note: If you must use a newer Python version and encounter errors, you will need to install the **Microsoft C++ Build Tools** via the Visual Studio Installer.)*

---

## Maintained by **Code with Thura**.

This toolkit was architected with a singular mission: to democratize studio-grade audio processing. By leveraging advanced neural networks and industry-standard broadcasting algorithms (EBU R128), we provide content creators with an automated pipeline that rivals expensive proprietary software—without the steep learning curve.

### Code of Conduct & Contribution
We believe in the power of open collaboration. This project is open-source to encourage innovation and transparency.
* **Feature Requests:** Have an idea for a new workflow? Open an issue.
* **Collaboration:** Feedback and pull requests are welcome. Please ensure new features are tested and documented.
* **Conduct:** We foster a professional, inclusive environment where knowledge sharing is paramount.
* **Integrity:** This software is provided "as is" for educational and productivity purposes. Please use it responsibly.

---