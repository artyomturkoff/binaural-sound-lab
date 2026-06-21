"""Reusable engine for binaural-style stereo experiments.

Experiment/preset files should import ``run_experiment`` from this module.
Normally, there is no need to edit this file when creating a new sound preset.
"""

import re

import numpy as np


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


def apply_left_right_swap(
    stereo: np.ndarray,
    sample_rate: int,
    swap_hz: float,
    transition_seconds: float = 0.005,
) -> np.ndarray:
    """Alternate the left and right channels at a full-cycle rate.

    One cycle starts with the original routing, swaps the channels halfway
    through, and returns to the original routing at the start of the next
    cycle. Short transitions prevent clicks at the swap boundaries.
    """
    if stereo.ndim != 2 or stereo.shape[1] != 2:
        raise ValueError("Audio must be a stereo array with exactly 2 channels.")
    if sample_rate <= 0:
        raise ValueError("Sample rate must be a positive integer.")
    if not np.isfinite(swap_hz):
        raise ValueError("LEFT_RIGHT_SWAP_HZ must be a finite number.")
    if swap_hz < 0:
        raise ValueError("LEFT_RIGHT_SWAP_HZ cannot be negative.")
    if transition_seconds < 0:
        raise ValueError("Swap transition duration cannot be negative.")
    if swap_hz == 0 or stereo.shape[0] == 0:
        return stereo.copy()
    if swap_hz > sample_rate / 2:
        raise ValueError(
            "LEFT_RIGHT_SWAP_HZ cannot exceed half the sample rate."
        )

    time = np.arange(stereo.shape[0], dtype=np.float64) / sample_rate
    half_cycle_position = time * (2.0 * swap_hz)
    half_cycle_number = np.floor(half_cycle_position).astype(np.int64)
    position_within_half = half_cycle_position - half_cycle_number
    target_is_swapped = (half_cycle_number % 2).astype(np.float64)

    half_cycle_seconds = 1.0 / (2.0 * swap_hz)
    effective_transition = min(transition_seconds, half_cycle_seconds)
    if effective_transition == 0:
        swap_mix = target_is_swapped
    else:
        transition_fraction = np.clip(
            position_within_half
            * half_cycle_seconds
            / effective_transition,
            0.0,
            1.0,
        )
        # Smoothstep has zero slope at both ends, reducing transition artifacts.
        transition_mix = transition_fraction**2 * (
            3.0 - 2.0 * transition_fraction
        )
        swap_mix = np.where(
            target_is_swapped == 1.0,
            transition_mix,
            1.0 - transition_mix,
        )
        # Playback has no preceding half-cycle to transition from.
        swap_mix = np.where(half_cycle_number == 0, 0.0, swap_mix)

    original_mix = 1.0 - swap_mix
    left = stereo[:, 0]
    right = stereo[:, 1]
    swapped = np.column_stack(
        (
            original_mix * left + swap_mix * right,
            original_mix * right + swap_mix * left,
        )
    )
    return swapped.astype(stereo.dtype, copy=False)


def make_stereo_audio(
    mode: str,
    notes: list[str],
    shift_channel: str,
    shift_hz: float,
    duration: float,
    sample_rate: int,
    volume: float,
    melody_repeats: int = 1,
    left_right_swap_hz: float = 0.0,
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

    stereo = (stereo * volume).astype(np.float32)
    return apply_left_right_swap(
        stereo,
        sample_rate,
        left_right_swap_hz,
    )


def play_audio(audio: np.ndarray, sample_rate: int) -> None:
    """Play stereo audio through the current default output device."""
    try:
        import sounddevice as sd
    except ImportError as error:
        raise RuntimeError(
            "The sounddevice package is not installed. Run: uv sync"
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
    left_right_swap_hz: float = 0.0,
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
    if left_right_swap_hz > 0:
        print(
            "Left/right swap: "
            f"{left_right_swap_hz:.2f} full cycles per second"
        )
    else:
        print("Left/right swap: disabled")
    if mode == "melody":
        print(f"Repeats: {melody_repeats}")
        print(
            f"Duration: {total_duration:.2f} seconds total "
            f"({duration:.2f} seconds per note)"
        )
    else:
        print(f"Duration: {total_duration:.2f} seconds")
    print(f"Sample rate: {sample_rate} Hz")
    print("Playing through the default audio output...\n")


def run_experiment(
    *,
    mode: str,
    notes: list[str],
    melody: list[str],
    duration_seconds: float,
    note_duration_seconds: float,
    melody_repeats: int,
    shift_channel: str,
    shift_hz: float,
    sample_rate: int,
    volume: float,
    left_right_swap_hz: float = 0.0,
) -> None:
    """Generate and play one experiment using settings from a preset file."""
    selected_mode = mode.lower().strip()
    selected_channel = shift_channel.lower().strip()

    if selected_mode == "chord":
        selected_notes = notes
        selected_duration = duration_seconds
        selected_repeats = 1
    elif selected_mode == "melody":
        selected_notes = melody
        selected_duration = note_duration_seconds
        selected_repeats = melody_repeats
    else:
        raise ValueError('MODE must be either "chord" or "melody".')

    # Generate first so invalid settings fail before playback is announced.
    audio = make_stereo_audio(
        mode=selected_mode,
        notes=selected_notes,
        shift_channel=selected_channel,
        shift_hz=shift_hz,
        duration=selected_duration,
        sample_rate=sample_rate,
        volume=volume,
        melody_repeats=selected_repeats,
        left_right_swap_hz=left_right_swap_hz,
    )

    print_playback_summary(
        mode=selected_mode,
        notes=selected_notes,
        shift_channel=selected_channel,
        shift_hz=shift_hz,
        duration=selected_duration,
        sample_rate=sample_rate,
        melody_repeats=selected_repeats,
        left_right_swap_hz=left_right_swap_hz,
    )
    play_audio(audio, sample_rate)
