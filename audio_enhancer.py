import os
import sys
import time
import shutil
import threading
import signal
import logging
from contextlib import contextmanager
import soundfile as sf
import pyloudnorm as pyln
from pydub import AudioSegment
from shutil import which

# --- DeepFilterNet Imports ---
from df.enhance import enhance, init_df, load_audio, save_audio

# ================= CONFIGURATION =================
# Target loudness level (Broadcast standard: -23)
TARGET_LOUDNESS = -23
DEFAULT_INPUT_FOLDER = "Source_Audio"

# Supported Input Formats
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma', '.aac', '.alac', '.aiff')

# Output & Temp Folders
OUTPUT_DIR = "Mastered_Audio_Output"
TEMP_CONVERT_DIR = "Temp_Conversion_Cache"
INTERMEDIATE_DIR = "Intermediate_Loudness_Norm"
# =================================================

# Global flags and model storage
is_loading = False
df_model = None
df_state = None

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    global is_loading
    is_loading = False
    print("\n\n" + "!" * 40)
    print(" Process interrupted by user. Exiting...")
    print("!" * 40 + "\n")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# --- SILENCING TOOLS ---
@contextmanager
def suppress_output():
    """Mutes stdout and stderr temporarily."""
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

def print_separator():
    print("\n" + "=" * 60 + "\n")

def spinner(message="Processing"):
    """Display a loading spinner in the terminal."""
    global is_loading
    spinner_chars = ["|", "/", "-", "\\"]
    idx = 0
    while is_loading:
        print(f"\r{message}... {spinner_chars[idx % len(spinner_chars)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print(f"\r{message}... Done!   ")

def check_dependencies():
    """Ensure essential tools exist."""
    if which("ffmpeg") is None and not os.path.exists("ffmpeg.exe"):
        print("Error: FFmpeg not found.")
        print("Please install FFmpeg or place ffmpeg.exe in this folder to handle .ogg/.mp3 files.")
        sys.exit(1)

def init_deepfilter_model():
    """Initialize the DeepFilterNet model once, silently."""
    global df_model, df_state
    try:
        print("Initializing DeepFilterNet Model (this may take a moment)...")
        
        # 1. Suppress the 'DF' logger (Python level logs)
        logging.getLogger("DF").setLevel(logging.ERROR)
        
        # 2. Suppress stdout/stderr (System level logs & git errors)
        with suppress_output():
            df_model, df_state, _ = init_df()
            
        print("Model loaded successfully.")
    except Exception as e:
        print(f"\nError loading DeepFilterNet model: {e}")
        sys.exit(1)

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
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(TEMP_CONVERT_DIR):
        os.makedirs(TEMP_CONVERT_DIR)
    if not os.path.exists(INTERMEDIATE_DIR):
        os.makedirs(INTERMEDIATE_DIR)

def convert_to_wav(file_path):
    global is_loading
    filename = os.path.basename(file_path)
    wav_path = os.path.join(TEMP_CONVERT_DIR, os.path.splitext(filename)[0] + ".wav")
    
    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=(f"Converting {filename}",))
        t.start()
        
        audio = AudioSegment.from_file(file_path)
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

def normalize_loudness(input_file):
    global is_loading
    filename = os.path.basename(input_file)
    output_path = os.path.join(INTERMEDIATE_DIR, filename)

    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Normalizing Loudness",))
        t.start()

        data, rate = sf.read(input_file)
        meter = pyln.Meter(rate)
        loudness = meter.integrated_loudness(data)
        
        normalized_audio = pyln.normalize.loudness(data, loudness, TARGET_LOUDNESS)
        sf.write(output_path, normalized_audio, rate)
        
        is_loading = False
        t.join()
        return output_path
    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nError normalizing {filename}: {e}")
        return None

def run_deepfilter(input_file):
    global is_loading, df_model, df_state
    base_name = os.path.basename(input_file)
    output_path = os.path.join(OUTPUT_DIR, base_name)
    
    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Enhancing Audio (DeepFilter)",))
        t.start()

        # Suppress output during load_audio as it might print warnings
        with suppress_output():
            audio, _ = load_audio(input_file, sr=df_state.sr())
            enhanced_audio = enhance(df_model, df_state, audio)
            save_audio(output_path, enhanced_audio, df_state.sr())

        is_loading = False
        t.join()
        
        if os.path.exists(output_path):
            return output_path
        return None

    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nDeepFilter Error on {input_file}: {e}")
        return None

def convert_to_final_mp3(wav_file, original_filename):
    global is_loading
    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Finalizing to .mp3",))
        t.start()
        
        name_no_ext = os.path.splitext(original_filename)[0]
        mp3_path = os.path.join(OUTPUT_DIR, f"{name_no_ext}.mp3")
        
        audio = AudioSegment.from_wav(wav_file)
        audio.export(mp3_path, format="mp3", bitrate="320k")
        
        try:
            os.remove(wav_file)
        except:
            pass

        is_loading = False
        t.join()
        return True
    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nError creating MP3: {e}")
        return False

def cleanup_folders(keep_normalized):
    print("\nPerforming cleanup...")
    if os.path.exists(TEMP_CONVERT_DIR):
        try:
            shutil.rmtree(TEMP_CONVERT_DIR)
        except Exception:
            pass

    if not keep_normalized:
        if os.path.exists(INTERMEDIATE_DIR):
            try:
                shutil.rmtree(INTERMEDIATE_DIR)
                print("Deleted intermediate files.")
            except Exception:
                pass
    else:
        print(f"Intermediate files saved in: {INTERMEDIATE_DIR}")

def main():
    try:
        print_separator()
        print("      PROFESSIONAL AUDIO MASTERING V2")
        print("      (Supports: .ogg, .flac, .wav, .mp3 -> Output: .mp3)")
        print_separator()

        check_dependencies()
        prepare_working_dirs()
        
        # Load Model ONCE (Silently)
        init_deepfilter_model()

        # Interactive Loop
        while True:
            files_to_process = get_input_files()
            
            if not files_to_process:
                if input("No files selected. Exit? (y/n): ").strip().lower() == 'y':
                    break
                else:
                    continue

            print(f"\nQueue: {len(files_to_process)} file(s) ready to process.")
            
            try:
                keep_norm_input = input("Save normalized intermediate files? (y/N): ").strip().lower()
                keep_normalized = keep_norm_input == 'y'
            except EOFError:
                break

            print_separator()

            for i, file_path in enumerate(files_to_process):
                original_filename = os.path.basename(file_path)
                print(f"[{i+1}/{len(files_to_process)}] Processing: {original_filename}")

                wav_file = convert_to_wav(file_path)
                if not wav_file: continue

                normalized_file = normalize_loudness(wav_file)
                if not normalized_file: continue

                enhanced_wav = run_deepfilter(normalized_file)
                
                if enhanced_wav:
                    if convert_to_final_mp3(enhanced_wav, original_filename):
                        print(f"Success: {original_filename}")
                else:
                    print(f"Failed: {original_filename}")
                
                print("-" * 30)

            cleanup_folders(keep_normalized)

            print_separator()
            print(f"Batch completed. Output in: {OUTPUT_DIR}")
            print_separator()
            
            cont = input("Process another batch? (y/n) [Enter = Yes]: ").strip().lower()
            if cont == 'n':
                break

    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()