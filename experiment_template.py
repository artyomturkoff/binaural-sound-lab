"""Copyable settings template for a binaural-style sound experiment.

To create another preset, copy this file, give the copy a descriptive name,
edit its settings, and run it with:

    cp experiment_template.py sandbox/your_preset_name.py
    uv run python sandbox/your_preset_name.py

The reusable audio code lives in binaural_engine.py and is installed by uv.
"""

from binaural_engine import run_experiment


# =============================================================================
# USER SETTINGS: edit these values in each preset file
# =============================================================================

# Use "chord" for one sustained note/chord, or "melody" for a note sequence.
MODE = "melody"

# Chord mode settings. A one-item list plays a single sustained note.
# NOTES = ["C3", "E3", "G3"]
NOTES = ["C4"]
DURATION_SECONDS = 10.0

# Melody mode settings. Every note has the same duration.
MELODY = [
    "C3",
    "D3",
    "E3",
    "F#3",
    "G#3",
    "A#3",
    "C4",
    "A#3",
    "G#3",
    "F#3",
    "E3",
    "D3",
]
NOTE_DURATION_SECONDS = 0.5
MELODY_REPEATS = 3

# The selected headphone channel receives SHIFT_HZ added to every frequency.
SHIFT_CHANNEL = "right"  # "left" or "right"
SHIFT_HZ = 8.0           # Positive or negative

# General audio settings.
SAMPLE_RATE = 48000
VOLUME = 0.25            # Keep this low when using headphones


if __name__ == "__main__":
    run_experiment(
        mode=MODE,
        notes=NOTES,
        melody=MELODY,
        duration_seconds=DURATION_SECONDS,
        note_duration_seconds=NOTE_DURATION_SECONDS,
        melody_repeats=MELODY_REPEATS,
        shift_channel=SHIFT_CHANNEL,
        shift_hz=SHIFT_HZ,
        sample_rate=SAMPLE_RATE,
        volume=VOLUME,
    )
