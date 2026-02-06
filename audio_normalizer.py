import os
import sys
import time
import shutil
import threading
import signal
import soundfile as sf
import pyloudnorm as pyln
from pydub import AudioSegment

# ================= CONFIGURATION =================
# Target Loudness in LUFS (TV/Broadcast: -23, Podcast/Web: -16 to -14)
TARGET_LOUDNESS = -23.0

# Folders
DEFAULT_INPUT_FOLDER = "Source_Audio"
OUTPUT_DIR = "Normalized_Audio_Output"
TEMP_DIR = "Temp_Conversion_Cache"

# Supported Input Formats
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma', '.aac', '.alac', '.aiff')
# =================================================

# Global flag for UI spinner
is_loading = False

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    global is_loading
    is_loading = False
    print("\n\n" + "!" * 40)
    print(" Process interrupted by user. Exiting...")
    print("!" * 40 + "\n")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def print_separator():
    print("\n" + "=" * 60 + "\n")

def spinner(message="Processing"):
    """Display a loading spinner."""
    global is_loading
    spinner_chars = ["|", "/", "-", "\\"]
    idx = 0
    while is_loading:
        print(f"\r{message}... {spinner_chars[idx % len(spinner_chars)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print(f"\r{message}... Done!   ")

def get_input_files():
    """Determine input source and return list of file paths."""
    print("Select Input Source:")
    print("1. Drag & drop a [File] or [Folder] here")
    print(f"2. Press [Enter] to use default folder: './{DEFAULT_INPUT_FOLDER}/'")
    
    try:
        user_input = input("\n> Path: ").strip().strip('"').strip("'")
    except EOFError:
        sys.exit(0)

    file_list = []

    # CASE 1: Default Folder
    if not user_input:
        target_dir = os.path.join(os.getcwd(), DEFAULT_INPUT_FOLDER)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print_separator()
            print(f"Created default folder: '{DEFAULT_INPUT_FOLDER}'")
            print("Please place your audio files inside it and run the script again.")
            print_separator()
            sys.exit(0)
        
        for f in os.listdir(target_dir):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                file_list.append(os.path.join(target_dir, f))
                
    # CASE 2: Dragged Directory
    elif os.path.isdir(user_input):
        print(f"Detected Folder: {user_input}")
        for f in os.listdir(user_input):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                file_list.append(os.path.join(user_input, f))

    # CASE 3: Single File
    elif os.path.isfile(user_input):
        print(f"Detected Single File: {user_input}")
        if user_input.lower().endswith(SUPPORTED_EXTENSIONS):
            file_list.append(user_input)
        else:
            print(f"\nError: File format not supported. Supported: {SUPPORTED_EXTENSIONS}")
            sys.exit(1)
            
    else:
        print(f"\nError: The path '{user_input}' is invalid.")
        sys.exit(1)
            
    return file_list

def prepare_working_dirs():
    """Create output and temp directories."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

def convert_to_wav(file_path):
    """Convert input to WAV for processing (if not already)."""
    global is_loading
    filename = os.path.basename(file_path)
    wav_path = os.path.join(TEMP_DIR, os.path.splitext(filename)[0] + ".wav")
    
    # If source is already WAV, just use it (or copy it to temp to be safe)
    if file_path.lower().endswith(".wav"):
        return file_path

    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=(f"Converting {filename}",))
        t.start()
        
        audio = AudioSegment.from_file(file_path)
        # Standardize to 48kHz for professional results
        audio = audio.set_frame_rate(48000)
        audio.export(wav_path, format="wav")
        
        is_loading = False
        t.join()
        return wav_path
    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nError converting {filename}: {e}")
        return None

def normalize_loudness(input_file, original_filename):
    """Measure and normalize loudness."""
    global is_loading
    
    # Construct output path (saving as WAV to preserve quality)
    name_no_ext = os.path.splitext(original_filename)[0]
    output_path = os.path.join(OUTPUT_DIR, f"{name_no_ext}_Normalized.wav")

    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Analyzing & Normalizing",))
        t.start()

        # Load audio
        data, rate = sf.read(input_file)
        
        # Measure Loudness
        meter = pyln.Meter(rate) 
        loudness_before = meter.integrated_loudness(data)
        
        # Normalize
        normalized_audio = pyln.normalize.loudness(data, loudness_before, TARGET_LOUDNESS)
        
        # Write to file
        sf.write(output_path, normalized_audio, rate)
        
        is_loading = False
        t.join()
        
        print(f"Loudness: {loudness_before:.2f} LUFS -> {TARGET_LOUDNESS:.2f} LUFS")
        return True
    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nError processing {original_filename}: {e}")
        return False

def cleanup_temp():
    """Remove temp files."""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception:
            pass

def main():
    try:
        print_separator()
        print("      PROFESSIONAL LOUDNESS NORMALIZER")
        print(f"      (Target: {TARGET_LOUDNESS} LUFS | Output: High-Quality WAV)")
        print_separator()

        # 1. Select Input
        files_to_process = get_input_files()
        
        if not files_to_process:
            print(f"\nNo valid audio files found.")
            return

        prepare_working_dirs()
        print(f"\nQueue: {len(files_to_process)} file(s) ready to process.")
        print_separator()

        # 2. Process Loop
        success_count = 0
        for i, file_path in enumerate(files_to_process):
            original_filename = os.path.basename(file_path)
            print(f"[{i+1}/{len(files_to_process)}] Processing: {original_filename}")

            # Convert if necessary
            wav_file = convert_to_wav(file_path)
            
            if wav_file:
                # Normalize
                if normalize_loudness(wav_file, original_filename):
                    success_count += 1
                    print("Status: Success")
                else:
                    print("Status: Failed")
            
            print("-" * 30)

        # 3. Cleanup & Exit
        cleanup_temp()
        
        print_separator()
        print(f"Completed {success_count}/{len(files_to_process)} files.")
        print(f"Files saved to: {OUTPUT_DIR}")
        print_separator()
        input("Press Enter to exit...")

    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()