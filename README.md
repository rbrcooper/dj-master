# DJ Master

A minimal-intervention Python script to automatically master your DJ mixes.

Built for house and techno mixes, this pipeline uses a deliberately light touch to preserve your original sound while protecting against clipping and ensuring a consistent loudness for sharing or streaming.

## What It Does
1. **High-pass filter (30Hz):** Removes sub-bass rumble and DC offset (which Pioneer CDJs/recorders sometimes introduce) without affecting audible frequencies.
2. **Soft limiter (-1dBTP):** A safety net that prevents digital clipping without heavily compressing the mix.
3. **Loudness normalization (-14 LUFS):** Normalizes the mix to the standard loudness target used by SoundCloud, Spotify, and Apple Music.
4. **Export:** Outputs a high-quality lossless `.wav` for your archives and a `320kbps .mp3` for easy sharing.

## Setup

1. Install Python 3.8+
2. Install [FFmpeg](https://ffmpeg.org/download.html) (required for the MP3 export step)
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script and provide the path to your raw mix:

```bash
python master.py "path/to/my_mix.wav"
```

The script will process the audio and create two new files in the same directory:
- `my_mix_mastered.wav`
- `my_mix_mastered.mp3`

## Configuration

You can tweak the processing parameters in `config.yaml`:
- `target_lufs`: Target loudness. `-14.0` is standard, but you can push it to `-12.0` if you want a louder master.
- `highpass_cutoff_hz`: Set to `30.0` to cut sub-bass noise.
- `limiter_threshold_db`: Set to `-1.0` to prevent clipping.
- `export_mp3`: Set to `true` or `false`.
- `mp3_bitrate`: Default is `"320k"`.
