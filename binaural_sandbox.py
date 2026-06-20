"""Simple binaural-style stereo tone experiments.

Edit the settings in the next section, then run:

    python binaural_sandbox.py

Channel 0 is left and channel 1 is right.
"""

import re

import numpy as np


# =============================================================================
# USER SETTINGS: edit these values to change the experiment
# =============================================================================

# Use "chord" for one sustained note/chord, or "melody" for a note sequence.
MODE = "chord"

# Chord mode settings. A one-item list plays a single sustained note.
NOTES = ["C3", "E3", "G3"]
# NOTES = ["A3"]
DURATION_SECONDS = 15.0

# Melody mode settings. Every note has the same duration.
MELODY = ["C4", "C4", "G4", "E4", "C4", "G4"]
NOTE_DURATION_SECONDS = 0.5
MELODY_REPEATS = 3  # Use 3 to play the complete melody three times

# The selected headphone channel receives SHIFT_HZ added to every frequency.
SHIFT_CHANNEL = "right"  # "left" or "right"
SHIFT_HZ = 10.0         # Positive or negative

# General audio settings.
SAMPLE_RATE = 48000
VOLUME = 0.25           # Keep this low when using headphones


# Semitone positions measured from C within an octave.
NOTE_OFFSETS = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


def note_to_frequency(note: str) -> float:
    """Convert a note name such as A4, C#4, or Db4 to frequency in hertz.

    Frequencies use twelve-tone equal temperament with A4 fixed at 440 Hz.
    Middle C (C4) is approximately 261.63 Hz.
    """
    if not isinstance(note, str):
        raise ValueError(f"Note must be text, received {note!r}.")

    match = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d+)", note.strip())
    if match is None:
        raise ValueError(
            f"Unknown note name {note!r}. "
            "Use names such as C4, F#3, Db4, or Bb5."
        )

    letter, accidental, octave_text = match.groups()
    semitone = NOTE_OFFSETS[letter.upper()]

    if accidental == "#":
        semitone += 1
    elif accidental == "b":
        semitone -= 1

    octave = int(octave_text)
    midi_note = 12 * (octave + 1) + semitone
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def sine_wave(freq: float, duration: float, sample_rate: int) -> np.ndarray:
    """Generate a mono sine wave."""
    if freq <= 0:
        raise ValueError(f"Frequency must be above 0 Hz, received {freq:.2f} Hz.")
    if duration <= 0:
        raise ValueError("Duration must be greater than 0 seconds.")
    if sample_rate <= 0:
        raise ValueError("Sample rate must be a positive integer.")

    sample_count = int(round(duration * sample_rate))
    time = np.arange(sample_count, dtype=np.float64) / sample_rate
    return np.sin(2.0 * np.pi * freq * time)


def apply_envelope(
    signal: np.ndarray,
    sample_rate: int,
    fade_seconds: float = 0.01,
) -> np.ndarray:
    """Apply short linear fade-in and fade-out ramps to prevent clicks."""
    if signal.size == 0:
        return signal.copy()
    if fade_seconds < 0:
        raise ValueError("Fade duration cannot be negative.")

    fade_samples = min(
        int(round(fade_seconds * sample_rate)),
        signal.size // 2,
    )
    if fade_samples == 0:
        return signal.copy()

    envelope = np.ones(signal.size, dtype=np.float64)
    fade = np.linspace(0.0, 1.0, fade_samples, endpoint=True)
    envelope[:fade_samples] = fade
    envelope[-fade_samples:] = fade[::-1]
    return signal * envelope


def shifted_frequency(note: str, frequency_shift_hz: float) -> float:
    """Return a note's synthesized frequency after a direct Hz offset."""
    frequency = note_to_frequency(note) + frequency_shift_hz
    if frequency <= 0:
        raise ValueError(
            f"Shifted frequency for {note!r} is {frequency:.2f} Hz. "
            "Reduce the negative SHIFT_HZ so every frequency stays above 0 Hz."
        )
    return frequency


def make_chord(
    notes: list[str],
    duration: float,
    sample_rate: int,
    frequency_shift_hz: float = 0.0,
) -> np.ndarray:
    """Create a mono chord by summing sine waves for all selected notes."""
    if not notes:
        raise ValueError("NOTES must contain at least one note.")

    waves = [
        sine_wave(
            shifted_frequency(note, frequency_shift_hz),
            duration,
            sample_rate,
        )
        for note in notes
    ]
    chord = np.sum(waves, axis=0)
    return apply_envelope(chord, sample_rate)


def make_melody(
    notes: list[str],
    note_duration: float,
    sample_rate: int,
    frequency_shift_hz: float = 0.0,
    repeats: int = 1,
) -> np.ndarray:
    """Create a repeated mono melody with equal-duration notes."""
    if not notes:
        raise ValueError("MELODY must contain at least one note.")
    if type(repeats) is not int or repeats < 1:
        raise ValueError("MELODY_REPEATS must be a positive integer.")

    note_signals = []
    for _ in range(repeats):
        for note in notes:
            tone = sine_wave(
                shifted_frequency(note, frequency_shift_hz),
                note_duration,
                sample_rate,
            )
            note_signals.append(apply_envelope(tone, sample_rate))

    return np.concatenate(note_signals)


def make_stereo_audio(
    mode: str,
    notes: list[str],
    shift_channel: str,
    shift_hz: float,
    duration: float,
    sample_rate: int,
    volume: float,
    melody_repeats: int = 1,
) -> np.ndarray:
    """Create normalized stereo audio with one frequency-shifted channel."""
    if shift_channel not in {"left", "right"}:
        raise ValueError('SHIFT_CHANNEL must be either "left" or "right".')
    if mode not in {"chord", "melody"}:
        raise ValueError('MODE must be either "chord" or "melody".')
    if not 0.0 <= volume <= 1.0:
        raise ValueError("VOLUME must be between 0.0 and 1.0.")

    left_shift = shift_hz if shift_channel == "left" else 0.0
    right_shift = shift_hz if shift_channel == "right" else 0.0

    if mode == "chord":
        left = make_chord(notes, duration, sample_rate, left_shift)
        right = make_chord(notes, duration, sample_rate, right_shift)
    else:
        left = make_melody(
            notes, duration, sample_rate, left_shift, melody_repeats
        )
        right = make_melody(
            notes, duration, sample_rate, right_shift, melody_repeats
        )

    stereo = np.column_stack((left, right))

    # Normalize both channels together to preserve their relative level, then
    # apply the user volume. The result cannot exceed the requested volume.
    peak = np.max(np.abs(stereo))
    if peak > 0.0:
        stereo = stereo / peak

    return (stereo * volume).astype(np.float32)


def play_audio(audio: np.ndarray, sample_rate: int) -> None:
    """Play stereo audio through the current default macOS output device."""
    try:
        import sounddevice as sd
    except ImportError as error:
        raise RuntimeError(
            "The sounddevice package is not installed. "
            "Run: python -m pip install -r requirements.txt"
        ) from error

    sd.play(audio, sample_rate)
    sd.wait()


def print_playback_summary(
    mode: str,
    notes: list[str],
    shift_channel: str,
    shift_hz: float,
    duration: float,
    sample_rate: int,
    melody_repeats: int = 1,
) -> None:
    """Print the important settings before playback."""
    total_duration = (
        duration
        if mode == "chord"
        else duration * len(notes) * melody_repeats
    )
    notes_label = "Notes" if mode == "chord" else "Melody"

    print("\nBinaural Sound Sandbox")
    print(f"Mode: {mode}")
    print(f"{notes_label}: {notes}")
    print(f"Shift: {shift_channel} channel, {shift_hz:+.2f} Hz")
    if mode == "melody":
        print(f"Repeats: {melody_repeats}")
        print(f"Duration: {total_duration:.2f} seconds total "
              f"({duration:.2f} seconds per note)")
    else:
        print(f"Duration: {total_duration:.2f} seconds")
    print(f"Sample rate: {sample_rate} Hz")
    print("Playing through the default audio output...\n")


def main() -> None:
    """Generate audio from the user settings and play it."""
    mode = MODE.lower().strip()

    if mode == "chord":
        selected_notes = NOTES
        duration = DURATION_SECONDS
        melody_repeats = 1
    elif mode == "melody":
        selected_notes = MELODY
        duration = NOTE_DURATION_SECONDS
        melody_repeats = MELODY_REPEATS
    else:
        raise ValueError('MODE must be either "chord" or "melody".')

    # Audio is generated before the summary so invalid settings fail before
    # the program announces that playback is starting.
    audio = make_stereo_audio(
        mode=mode,
        notes=selected_notes,
        shift_channel=SHIFT_CHANNEL.lower().strip(),
        shift_hz=SHIFT_HZ,
        duration=duration,
        sample_rate=SAMPLE_RATE,
        volume=VOLUME,
        melody_repeats=melody_repeats,
    )

    print_playback_summary(
        mode=mode,
        notes=selected_notes,
        shift_channel=SHIFT_CHANNEL.lower().strip(),
        shift_hz=SHIFT_HZ,
        duration=duration,
        sample_rate=SAMPLE_RATE,
        melody_repeats=melody_repeats,
    )
    play_audio(audio, SAMPLE_RATE)


if __name__ == "__main__":
    main()
