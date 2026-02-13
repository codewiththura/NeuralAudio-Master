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
TARGET_LOUDNESS = -23
DEFAULT_INPUT_FOLDER = "Source_Audio"
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma', '.aac', '.alac', '.aiff')
OUTPUT_DIR = "Mastered_Audio_Output"
TEMP_CONVERT_DIR = "Temp_Conversion_Cache"
INTERMEDIATE_DIR = "Intermediate_Loudness_Norm"
# =================================================

is_loading = False
df_model = None
df_state = None

def signal_handler(sig, frame):
    global is_loading
    is_loading = False
    print("\n\n" + "!" * 40)
    print(" Process interrupted by user. Exiting...")
    print("!" * 40 + "\n")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

@contextmanager
def suppress_output():
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
    print("\n" + "=" * 60 + "\n", flush=True)

def spinner(message="Processing"):
    global is_loading
    spinner_chars = ["|", "/", "-", "\\"]
    idx = 0
    while is_loading:
        print(f"\r{message}... {spinner_chars[idx % len(spinner_chars)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print(f"\r{message}... Done!   ", flush=True)

def check_dependencies():
    if which("ffmpeg") is None and not os.path.exists("ffmpeg.exe"):
        print("\nError: FFmpeg not found.", flush=True)
        sys.exit(1)

def init_deepfilter_model():
    """Initialize the DeepFilterNet model with a spinner for feedback."""
    global df_model, df_state, is_loading
    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Initializing AI Model (this may take a moment)",))
        t.start()
        
        logging.getLogger("DF").setLevel(logging.ERROR)
        
        with suppress_output():
            # This is the heavy lifting
            df_model, df_state, _ = init_df()
            
        is_loading = False
        t.join()
    except Exception as e:
        is_loading = False
        print(f"\nError loading model: {e}", flush=True)
        sys.exit(1)

def get_input_files():
    print("\n[READY] Please specify the audio source:", flush=True)
    print("  > Drag & Drop a folder or file")
    print(f"  > Press [ENTER] for default: ./{DEFAULT_INPUT_FOLDER}/")
    print("  > Type 'q' or 'exit' to quit")
    
    try:
        user_input = input("\n> Path: ").strip().strip('"').strip("'")
    except EOFError:
        sys.exit(0)
        
    if user_input.lower() in ['q', 'quit', 'exit']:
        return "QUIT"

    file_list = []
    if not user_input:
        target_dir = os.path.join(os.getcwd(), DEFAULT_INPUT_FOLDER)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created default folder: '{DEFAULT_INPUT_FOLDER}'", flush=True)
        
        for f in os.listdir(target_dir):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                file_list.append(os.path.join(target_dir, f))
                
    elif os.path.isdir(user_input):
        for f in os.listdir(user_input):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                file_list.append(os.path.join(user_input, f))

    elif os.path.isfile(user_input):
        if user_input.lower().endswith(SUPPORTED_EXTENSIONS):
            file_list.append(user_input)
            
    return file_list

def prepare_working_dirs():
    for d in [OUTPUT_DIR, TEMP_CONVERT_DIR, INTERMEDIATE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)

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
        return None

def run_deepfilter(input_file):
    global is_loading, df_model, df_state
    base_name = os.path.basename(input_file)
    output_path = os.path.join(OUTPUT_DIR, base_name)
    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Enhancing Audio (DeepFilter)",))
        t.start()
        with suppress_output():
            audio, _ = load_audio(input_file, sr=df_state.sr())
            enhanced_audio = enhance(df_model, df_state, audio)
            save_audio(output_path, enhanced_audio, df_state.sr())
        is_loading = False
        t.join()
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        is_loading = False
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
        if os.path.exists(wav_file): os.remove(wav_file)
        is_loading = False
        t.join()
        return True
    except Exception as e:
        is_loading = False
        return False

def cleanup_folders(keep_normalized):
    if os.path.exists(TEMP_CONVERT_DIR):
        shutil.rmtree(TEMP_CONVERT_DIR, ignore_errors=True)
    if not keep_normalized and os.path.exists(INTERMEDIATE_DIR):
        shutil.rmtree(INTERMEDIATE_DIR, ignore_errors=True)

def main():
    try:
        print_separator()
        print("      PROFESSIONAL AUDIO MASTERING V2", flush=True)
        print("      (Supports: .ogg, .flac, .wav, .mp3 -> Output: .mp3)", flush=True)
        print_separator()

        check_dependencies()
        prepare_working_dirs()
        
        init_deepfilter_model()

        while True:
            files_to_process = get_input_files()
            if files_to_process == "QUIT":
                print("\nShutting down. Goodbye!", flush=True)
                break
            if not files_to_process:
                print("\n[!] No valid files found. Try again.", flush=True)
                continue

            print(f"\nQueue: {len(files_to_process)} file(s) ready.", flush=True)
            keep_norm_input = input("Save normalized files? (y/N): ").strip().lower()
            keep_normalized = keep_norm_input == 'y'

            print_separator()

            for i, file_path in enumerate(files_to_process):
                original_filename = os.path.basename(file_path)
                print(f"[{i+1}/{len(files_to_process)}] Processing: {original_filename}", flush=True)

                wav_file = convert_to_wav(file_path)
                if not wav_file: continue

                norm_file = normalize_loudness(wav_file)
                if not norm_file: continue

                enhanced_wav = run_deepfilter(norm_file)
                if enhanced_wav:
                    if convert_to_final_mp3(enhanced_wav, original_filename):
                        print(f"Success: {original_filename}", flush=True)
                
                print("-" * 30, flush=True)

            cleanup_folders(keep_normalized)
            print_separator()
            
            cont = input("Process next batch? (Y/n): ").strip().lower()
            if cont == 'n': break

    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()