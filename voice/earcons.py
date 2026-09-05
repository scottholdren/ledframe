"""Earcons: short synthesized cues the wall uses instead of speech.

    heard    you stopped talking and we caught it        (rising blip)
    working  Claude is generating                         (soft tick, loop it)
    done     animation is on the wall                     (ascending resolve)
    unheard  didn't catch that / wake word with no speech (falling pair)
    error    generation failed / validation rejected      (short dissonant buzz)

Rendered to WAV on first use (cache dir), played with aplay. No audio libs.

    python -m voice.earcons            # play them all, in order
    python -m voice.earcons done       # play one
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

RATE = 48_000
CACHE = Path(os.environ.get("LEDFRAME_EARCON_DIR", "/tmp/ledframe-earcons"))
SPEAKER = os.environ.get("LEDFRAME_SPEAKER", "plughw:0,0")
GAIN = float(os.environ.get("LEDFRAME_EARCON_GAIN", "0.5"))


def _tone(freq: float, ms: float, *, attack=0.004, decay=None, harmonics=(1.0,), phase=0.0) -> np.ndarray:
    n = int(RATE * ms / 1000)
    t = np.arange(n) / RATE
    x = np.zeros(n)
    for k, amp in enumerate(harmonics, start=1):
        x += amp * np.sin(2 * np.pi * freq * k * t + phase)
    x /= sum(abs(a) for a in harmonics)
    env = np.ones(n)
    a = int(RATE * attack)
    env[:a] = np.linspace(0, 1, a)
    if decay is None:
        decay = ms / 1000 * 0.6
    env *= np.exp(-t / decay)
    r = min(n, int(RATE * 0.006))
    env[-r:] *= np.linspace(1, 0, r)
    return x * env


def _seq(*parts: np.ndarray, gap_ms: float = 0.0) -> np.ndarray:
    gap = np.zeros(int(RATE * gap_ms / 1000))
    out = []
    for i, p in enumerate(parts):
        out.append(p)
        if i < len(parts) - 1:
            out.append(gap)
    return np.concatenate(out)


def _mix(*parts: np.ndarray) -> np.ndarray:
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p
    return out / len(parts)


# A little warmth: fundamental + quiet 2nd/3rd harmonics reads as a soft mallet.
SOFT = (1.0, 0.25, 0.08)


def synth(name: str) -> np.ndarray:
    if name == "heard":
        return _seq(_tone(660, 70, harmonics=SOFT), _tone(990, 110, harmonics=SOFT), gap_ms=10)
    if name == "working":
        return _tone(1320, 28, attack=0.001, decay=0.012, harmonics=(1.0, 0.1))
    if name == "done":
        return _seq(_tone(523.25, 90, harmonics=SOFT),
                    _tone(659.25, 90, harmonics=SOFT),
                    _tone(783.99, 260, harmonics=SOFT, decay=0.16), gap_ms=15)
    if name == "unheard":
        return _seq(_tone(880, 120, harmonics=SOFT, decay=0.08),
                    _tone(660, 200, harmonics=SOFT, decay=0.12), gap_ms=20)
    if name == "error":
        buzz = _mix(_tone(220, 240, harmonics=(1.0, 0, 0.33, 0, 0.2), decay=0.4),
                    _tone(233, 240, harmonics=(1.0, 0, 0.33, 0, 0.2), decay=0.4))
        return _seq(buzz, buzz, gap_ms=60)
    raise KeyError(name)


NAMES = ("heard", "working", "done", "unheard", "error")


def path(name: str) -> Path:
    return CACHE / f"{name}.wav"


def render(name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    x = synth(name) * GAIN
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path(name)), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    return path(name)


def ensure() -> None:
    for n in NAMES:
        if not path(n).exists():
            render(n)


def play(name: str, *, block: bool = True) -> subprocess.Popen | None:
    ensure()
    p = subprocess.Popen(["aplay", "-q", "-D", SPEAKER, str(path(name))],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if block:
        p.wait()
        return None
    return p


def main(argv: list[str]) -> None:
    for n in NAMES:
        render(n)
    names = argv or list(NAMES)
    for n in names:
        print(n, flush=True)
        play(n)
        if n == "working":
            for _ in range(3):
                time.sleep(0.7)
                play("working")
        time.sleep(0.9)


if __name__ == "__main__":
    main(sys.argv[1:])
