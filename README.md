# Winamp Classic HD (2K / 4K)

The Classic Winamp look, redrawn at 1.5×, 2×, 3× and 4× so it stays sharp on 1440p and 4K displays.

Classic skins (`.wsz`) are locked to a 275×116 px main window and can only be pixel-doubled. This project rebuilds the same layout as a **Modern (freeform) skin** (`.wal`), with every bitmap rendered natively at the target size.

![Preview](docs/preview.png)

*Preview is a mock-up composed by the generator, not a screenshot.*

## Downloads

Ready-to-install builds are in [`dist/`](dist/) (skin version 1.24):

| File | Main window | Suggested for |
|---|---|---|
| `Classic HD x1.5.wal` | 413×174 | 1440p |
| `Classic HD x2.wal` | 550×232 | 1440p (large) or 4K (small) |
| `Classic HD x3.wal` | 825×348 | 4K |
| `Classic HD x4.wal` | 1100×464 | 4K |

## Install

1. Double-click a `.wal` file and confirm the "install this Winamp Skin?" prompt, **or** copy it into `C:\Program Files (x86)\Winamp\Skins`.
2. Pick it under **Options → Skins**.

Developed and tested on **Winamp 5.8 (build 3660)** on Windows 11. It needs the Modern skin engine (`gen_ff.dll`), which ships with Winamp 5.x.

## What's in the skin

- **Main window** – Classic layout: clock, visualizer, scrolling song title, kbps / kHz, mono / stereo, volume, balance, seek bar, transport, shuffle / repeat, EQ / PL toggles, windowshade mode.
- **Equalizer** – preamp + 10 bands, ON / AUTO / PRESETS.
- **Playlist** – resizable, ADD / REM / SEL / MISC / LIST, total-time readout, centred title.
- **Library, Video, Visualization** – resizable frames in the same style.

Classic details that were reproduced:

- Clock digits use the original Classic digit shapes (9×13, 1 px strokes), redrawn as vectors.
- Volume, balance and EQ bars are a single colour that follows the slider value (green → yellow → orange → red).
- Song title always scrolls with a `***` separator, even when it is short enough to fit (as in Classic).
- Gold seek handle, three-line volume / balance handles.

## Known gaps

- No track number (`1.`) in front of the song title.
- No EQ curve graph; the O-A-I-D-V letters are decorative.
- Playlist has no windowshade mode.
- The playlist's track list is drawn by Winamp itself; its font size is set in **Preferences → Playlist**, not by the skin.
- kbps / kHz digits are centred in their boxes rather than right-aligned.
- Video and Visualization windows, and window resizing, have had little testing.

## Build from source

Requirements: Python 3, [Pillow](https://python-pillow.org/), and Liberation Sans (or DejaVu Sans) Bold/Regular installed under `/usr/share/fonts/truetype/`.

```sh
python3 gen.py <scale> <outdir>
# e.g. build all four sizes (fractional scales such as 1.5 work)
for s in 1.5 2 3 4; do python3 gen.py $s out; done
```

Each run writes `out/Classic HD x<scale>/` (unpacked skin), `out/Classic HD x<scale>.wal` (installable) and `out/preview_x<scale>.png`.

Everything — bitmaps, XML and packaging — is produced by the single script [`gen.py`](gen.py). Coordinates are written in Classic units (275×116) and multiplied by the scale.

## How a few things work

- **Value-coloured bars without scripts.** A hidden second slider bound to the same value carries a huge gradient image as its "thumb". A groove-sized group clips it, so the groove shows one near-uniform colour that changes with the value.
- **Resizable windows need a region.** A layout with no background image has an empty window region; each frame sits in a group with `background` + `sysregion="1"`, otherwise the window exists but is invisible.
- **Bitmap-font text is clipped if the text box is not wider than the text**, so the kbps / kHz / playlist-time boxes are deliberately oversized and positioned by measurement.

## Third-party files

`assets/songinfo.maki` and `assets/titlebar.maki` are compiled scripts taken unmodified from the **Winamp Modern** skin that ships with Winamp 5.8. They drive the kbps / kHz / mono-stereo display and keep window titles centred. They are © their respective owners (Nullsoft / Winamp) and are included only because the skin cannot provide those two behaviours without them. Everything else in this repository was written for this project.

Winamp is a trademark of its respective owner. This is an unofficial fan skin.
