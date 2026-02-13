import os
import sys
import time
import shutil
import threading
import signal
import av  # PyAV
import soundfile as sf
import pyloudnorm as pyln

# ================= CONFIGURATION =================
# Folders
DEFAULT_INPUT_FOLDER = "Source_Audio"
OUTPUT_DIR = "Normalized_Audio_Output"
TEMP_DIR = "Temp_Conversion_Cache"

# Supported Input Formats
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma', '.aac', '.alac', '.aiff')

# Loudness Presets
LOUDNESS_PRESETS = {
    "1": {"name": "TV / Broadcast (EBU R128)", "lufs": -23.0},
    "2": {"name": "Podcast / Mobile (AES)", "lufs": -16.0},
    "3": {"name": "Music Streaming (Spotify/YT)", "lufs": -14.0},
}
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

def get_target_loudness():
    """Ask user to select a loudness target."""
    print("Select Target Loudness:")
    for key, preset in LOUDNESS_PRESETS.items():
        print(f"{key}. {preset['name']}: {preset['lufs']} LUFS")
    print("4. Custom Value")

    while True:
        choice = input("\n> Select option (1-4) [Default: 1]: ").strip()
        
        if not choice:
            return -23.0  # Default to Broadcast
            
        if choice in LOUDNESS_PRESETS:
            return LOUDNESS_PRESETS[choice]["lufs"]
        
        if choice == "4":
            try:
                custom_val = float(input("Enter target LUFS (e.g. -18.0): "))
                if -70 < custom_val < 0:
                    return custom_val
                else:
                    print("Error: Value must be between -70 and 0.")
            except ValueError:
                print("Error: Invalid number.")
        else:
            print("Invalid selection. Please try again.")

def get_input_files():
    """Determine input source and return list of file paths."""
    print_separator()
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
            print("Created default folder. Please add files and run again.")
            return []
        
        for f in os.listdir(target_dir):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                file_list.append(os.path.join(target_dir, f))
                
    # CASE 2: Dragged Directory
    elif os.path.isdir(user_input):
        for f in os.listdir(user_input):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                file_list.append(os.path.join(user_input, f))

    # CASE 3: Single File
    elif os.path.isfile(user_input):
        if user_input.lower().endswith(SUPPORTED_EXTENSIONS):
            file_list.append(user_input)
            
    else:
        print(f"\nError: The path '{user_input}' is invalid.")
        return []
            
    return file_list

def prepare_working_dirs():
    """Create output and temp directories."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

def convert_to_wav(file_path):
    """Convert input to WAV using PyAV (if not already WAV)."""
    global is_loading
    filename = os.path.basename(file_path)
    wav_path = os.path.join(TEMP_DIR, os.path.splitext(filename)[0] + ".wav")
    
    if file_path.lower().endswith(".wav"):
        return file_path

    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=(f"Converting {filename}",))
        t.start()
        
        with av.open(file_path) as input_container:
            in_stream = input_container.streams.audio[0]
            with av.open(wav_path, mode='w', format='wav') as output_container:
                out_stream = output_container.add_stream('pcm_s16le', rate=48000)
                out_stream.layout = 'stereo'
                resampler = av.AudioResampler(format='s16', layout='stereo', rate=48000)

                for packet in input_container.demux(in_stream):
                    for frame in packet.decode():
                        frame.pts = None
                        out_frames = resampler.resample(frame)
                        for out_frame in out_frames:
                            for packet in out_stream.encode(out_frame):
                                output_container.mux(packet)
                for packet in out_stream.encode(None):
                    output_container.mux(packet)

        is_loading = False
        t.join()
        return wav_path

    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nError converting {filename}: {e}")
        return None

def normalize_loudness(input_file, original_filename, target_lufs):
    """Measure and normalize loudness to target_lufs."""
    global is_loading
    
    name_no_ext = os.path.splitext(original_filename)[0]
    output_path = os.path.join(OUTPUT_DIR, f"{name_no_ext}_Normalized.wav")

    try:
        is_loading = True
        t = threading.Thread(target=spinner, args=("Analyzing & Normalizing",))
        t.start()

        data, rate = sf.read(input_file)
        meter = pyln.Meter(rate) 
        loudness_before = meter.integrated_loudness(data)
        
        normalized_audio = pyln.normalize.loudness(data, loudness_before, target_lufs)
        sf.write(output_path, normalized_audio, rate)
        
        is_loading = False
        t.join()
        
        print(f"Loudness: {loudness_before:.2f} -> {target_lufs:.2f} LUFS")
        return True
    except Exception as e:
        is_loading = False
        t.join()
        print(f"\nError processing {original_filename}: {e}")
        return False

def cleanup_temp():
    if os.path.exists(TEMP_DIR):
        try: shutil.rmtree(TEMP_DIR)
        except: pass

def main():
    try:
        print_separator()
        print("      PROFESSIONAL LOUDNESS NORMALIZER")
        print_separator()

        while True:
            # 1. Select Loudness Target
            target_lufs = get_target_loudness()

            # 2. Select Input
            files_to_process = get_input_files()
            
            if not files_to_process:
                print(f"\nNo valid audio files found.")
                retry = input("Try again? (Y/n): ").strip().lower()
                if retry == 'n' or retry == 'q':
                    print("Exiting...")
                    break
                continue

            prepare_working_dirs()
            print(f"\nTarget: {target_lufs} LUFS | Queue: {len(files_to_process)} files")
            print_separator()

            # 3. Process Loop
            success_count = 0
            for i, file_path in enumerate(files_to_process):
                original_filename = os.path.basename(file_path)
                print(f"[{i+1}/{len(files_to_process)}] Processing: {original_filename}")

                wav_file = convert_to_wav(file_path)
                
                if wav_file:
                    if normalize_loudness(wav_file, original_filename, target_lufs):
                        success_count += 1
                        print("Status: Success")
                    else:
                        print("Status: Failed")
                
                print("-" * 30)

            cleanup_temp()
            
            print_separator()
            print(f"Completed {success_count}/{len(files_to_process)} files.")
            print(f"Files saved to: {OUTPUT_DIR}")
            print_separator()
            
            # 4. Restart or Exit?
            restart = input("Start a new process? (Y/n/q) [Default: Y]: ").strip().lower()
            if restart == 'n' or restart == 'q':
                print("Exiting...")
                break
            
            print("\n" * 2)

    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()