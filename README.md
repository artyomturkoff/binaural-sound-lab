# Binaural Sound Sandbox

A small Python project for experimenting with binaural-style stereo tones through
headphones. One channel plays the normal piano-note frequencies, while the
selected channel plays those frequencies with a fixed number of hertz added.

For example, with A4 (440 Hz), `SHIFT_CHANNEL = "left"`, and
`SHIFT_HZ = 10.0`:

- Left channel: 450 Hz
- Right channel: 440 Hz

This is direct sine-wave synthesis, not pitch-shifting DSP. The project supports
a sustained note/chord mode and a simple equal-duration melody mode.

## Project files

- `binaural_engine.py` contains the reusable synthesis and playback functions.
  You normally do not need to edit it.
- `experiment_template.py` is a settings template. Copy it whenever you want to
  save a new chord or melody preset.
- `sandbox/` contains your named experiment presets.

The engine is installed as part of the local uv project, so preset files inside
`sandbox/` can import it without changing Python paths.

## Requirements

- Python 3.10 or newer
- Headphones connected
- NumPy
- sounddevice

## Install with uv

Open Terminal in this project folder and install the dependencies:

```bash
uv sync
```

The project installation performed by `uv sync` makes `binaural_engine`
available to scripts inside `sandbox/`.

The `sounddevice` package normally includes what it needs on macOS. If it
reports a PortAudio error, install PortAudio with Homebrew and retry:

```bash
brew install portaudio
uv sync
```

Before running the program, select the connected headphones in macOS under
**System Settings > Sound > Output**.

## Run

```bash
uv run python sandbox/experiment_template.py
```

The program prints the selected settings, generates a stereo NumPy array, and
plays it using the current macOS default output device.

## Create named presets

From the project root, copy the settings template into `sandbox/` and give it a
descriptive name:

```bash
cp experiment_template.py sandbox/calming_melody.py
```

Edit the settings inside `sandbox/calming_melody.py`, then run that preset:

```bash
uv run python sandbox/calming_melody.py
```

You can also enter the sandbox directory and run a preset there:

```bash
cd sandbox
uv run python calming_melody.py
```

uv finds the project configuration in the parent directory.

You can keep as many preset files as you like:

```text
binaural_engine.py
experiment_template.py
sandbox/
  experiment_template.py
  calming_melody.py
  c_major_chord.py
  eight_hz_sequence.py
```

Only copy files inside `sandbox/`. All presets share the functions in
`binaural_engine.py`; do not copy the engine.

## Chord or single-note mode

Edit the settings in your chosen preset file:

```python
MODE = "chord"

NOTES = ["C4", "E4", "G4"]
# For one note, use something like:
# NOTES = ["A4"]

SHIFT_CHANNEL = "left"
SHIFT_HZ = 10.0
DURATION_SECONDS = 5.0
SAMPLE_RATE = 44100
VOLUME = 0.25
```

All notes in `NOTES` are summed into one sustained chord. Sharps and flats are
accepted, including names such as `C#4`, `Db4`, `F#3`, and `Bb5`.

## Melody mode

Change `MODE` and edit the melody settings:

```python
MODE = "melody"

MELODY = ["C4", "C4", "G4", "E4", "C4", "G4"]
NOTE_DURATION_SECONDS = 0.25
MELODY_REPEATS = 3

SHIFT_CHANNEL = "right"
SHIFT_HZ = 10.0
SAMPLE_RATE = 44100
VOLUME = 0.25
```

Every melody note lasts exactly `NOTE_DURATION_SECONDS`. Set
`MELODY_REPEATS = 3` to play the complete list of notes three times, or use `1`
to play it once. This simple project does not include rests, tempo, or a rhythm
engine.

## Hearing safety

Keep `VOLUME` low, especially when using headphones. Start below `0.25`, listen
briefly, and increase only if necessary. Stop playback immediately if the sound
is uncomfortable. This project is for programming and audio experiments, not
for medical or therapeutic use.
