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

## Requirements

- Python 3.11.9 or newer
- Headphones connected
- NumPy
- sounddevice

## Install on macOS

Open Terminal in this project folder and create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `sounddevice` package normally installs its audio dependency automatically
on macOS. If installation reports a PortAudio error, install it with Homebrew
and then retry:

```bash
brew install portaudio
python -m pip install -r requirements.txt
```

Before running the program, select the connected headphones in macOS under
**System Settings > Sound > Output**.

## Run

```bash
python binaural_sandbox.py
```

The program prints the selected settings, generates a stereo NumPy array, and
plays it using the current macOS default output device.

## Chord or single-note mode

Edit the settings near the top of `binaural_sandbox.py`:

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

SHIFT_CHANNEL = "right"
SHIFT_HZ = 10.0
SAMPLE_RATE = 44100
VOLUME = 0.25
```

Every melody note lasts exactly `NOTE_DURATION_SECONDS`. This simple project
does not include rests, tempo, or a rhythm engine.

## Hearing safety

Keep `VOLUME` low, especially when using headphones. Start below `0.25`, listen
briefly, and increase only if necessary. Stop playback immediately if the sound
is uncomfortable. This project is for programming and audio experiments, not
for medical or therapeutic use.
