import sys
import os
import subprocess
import tempfile
import yaml
import soundfile as sf
import pyloudnorm as pyln
from pedalboard import Pedalboard, HighpassFilter, Limiter


def load_config(config_path="config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)["mastering"]
    return {
        "target_lufs": -14.0,
        "highpass_cutoff_hz": 30.0,
        "dynaudnorm_frame_ms": 500,
        "dynaudnorm_smoothing": 15,
        "limiter_threshold_db": -1.0,
        "export_mp3": True,
        "mp3_bitrate": "320k"
    }


def run_dynaudnorm(input_wav, output_wav, frame_ms=500, smoothing=15):
    """Use ffmpeg's dynaudnorm to balance quiet and loud sections across the mix."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_wav,
        "-af", f"dynaudnorm=f={frame_ms}:g={smoothing}",
        output_wav
    ]
    print(f"Running dynamic normalizer (window={frame_ms}ms, smoothing={smoothing})...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: ffmpeg dynaudnorm failed.\n{result.stderr}")
            sys.exit(1)
    except FileNotFoundError:
        print("Error: ffmpeg is not installed or not found in PATH.")
        print("Please install ffmpeg to use the dynamic normalizer and export to MP3.")
        print("Download: https://ffmpeg.org/download.html")
        sys.exit(1)


def export_mp3(wav_path, mp3_path, bitrate="320k"):
    """Export to MP3 using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-b:a", bitrate,
        mp3_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: MP3 export failed.\n{result.stderr}")
    else:
        print(f"MP3 saved: {mp3_path}")


def process_audio(input_file):
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    config = load_config()
    target_lufs = config.get("target_lufs", -14.0)
    hp_freq = config.get("highpass_cutoff_hz", 30.0)
    limiter_thresh = config.get("limiter_threshold_db", -1.0)
    frame_ms = config.get("dynaudnorm_frame_ms", 500)
    smoothing = config.get("dynaudnorm_smoothing", 15)

    base_name, _ = os.path.splitext(input_file)
    out_wav = f"{base_name}_mastered.wav"
    out_mp3 = f"{base_name}_mastered.mp3"

    # Step 1: High-pass filter via pedalboard
    print(f"Loading {input_file}...")
    data, rate = sf.read(input_file)
    print(f"Applying high-pass filter at {hp_freq}Hz...")
    board = Pedalboard([HighpassFilter(cutoff_frequency_hz=hp_freq)])
    data = board(data, rate)

    # Write to a temp file for ffmpeg to process
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    sf.write(tmp_path, data, rate)

    # Step 2: Dynamic normalization via ffmpeg dynaudnorm
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp2:
        tmp2_path = tmp2.name
    run_dynaudnorm(tmp_path, tmp2_path, frame_ms=frame_ms, smoothing=smoothing)
    os.remove(tmp_path)

    # Step 3: Integrated loudness normalization via pyloudnorm
    print("Measuring integrated loudness...")
    data, rate = sf.read(tmp2_path)
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    print(f"Loudness after dynaudnorm: {loudness:.2f} LUFS")
    print(f"Normalizing to {target_lufs} LUFS...")
    data = pyln.normalize.loudness(data, loudness, target_lufs)

    # Step 4: Safety limiter via pedalboard
    print(f"Applying limiter at {limiter_thresh}dB...")
    board = Pedalboard([Limiter(threshold_db=limiter_thresh)])
    data = board(data, rate)

    # Step 5: Export
    print(f"Saving WAV: {out_wav}")
    sf.write(out_wav, data, rate)
    os.remove(tmp2_path)

    if config.get("export_mp3", True):
        export_mp3(out_wav, out_mp3, bitrate=config.get("mp3_bitrate", "320k"))

    print("\nDone!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python master.py <input_audio_file>")
        sys.exit(1)

    process_audio(sys.argv[1])
