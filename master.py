import sys
import os
import yaml
import soundfile as sf
import pyloudnorm as pyln
from pedalboard import Pedalboard, HighpassFilter, Limiter
from pydub import AudioSegment

def load_config(config_path="config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)["mastering"]
    # Fallback default configuration
    return {
        "target_lufs": -14.0,
        "highpass_cutoff_hz": 30.0,
        "limiter_threshold_db": -1.0,
        "export_mp3": True,
        "mp3_bitrate": "320k"
    }

def process_audio(input_file):
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print(f"Loading {input_file}...")
    data, rate = sf.read(input_file)
    
    config = load_config()
    target_lufs = config["target_lufs"]
    hp_freq = config["highpass_cutoff_hz"]
    limiter_thresh = config["limiter_threshold_db"]

    print("Building pedalboard chain...")
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=hp_freq),
        Limiter(threshold_db=limiter_thresh)
    ])

    print(f"Applying effects (Highpass {hp_freq}Hz + Limiter {limiter_thresh}dB)...")
    processed = board(data, rate)

    print("Measuring loudness...")
    meter = pyln.Meter(rate) # create BS.1770 meter
    loudness = meter.integrated_loudness(processed)
    print(f"Current Loudness: {loudness:.2f} LUFS")

    print(f"Normalizing to {target_lufs} LUFS...")
    normalized = pyln.normalize.loudness(processed, loudness, target_lufs)

    # Prepare output filenames
    base_name, _ = os.path.splitext(input_file)
    out_wav = f"{base_name}_mastered.wav"
    out_mp3 = f"{base_name}_mastered.mp3"

    print(f"Saving WAV to {out_wav}...")
    sf.write(out_wav, normalized, rate)

    if config.get("export_mp3", True):
        print(f"Converting to MP3 ({out_mp3})...")
        try:
            audio = AudioSegment.from_wav(out_wav)
            audio.export(out_mp3, format="mp3", bitrate=config.get("mp3_bitrate", "320k"))
            print("MP3 saved successfully.")
        except Exception as e:
            print(f"Error saving MP3 (is ffmpeg installed?): {e}")

    print("Mastering complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python master.py <input_audio_file>")
        sys.exit(1)
    
    process_audio(sys.argv[1])
