"""Earcons: short synthesized cues the wall uses instead of speech.

    listening  wake word heard; wall glows blue + shimmers   slow minor bloom that brightens   ✔
    heard      you stopped talking, we caught it            the bloom inverted, closing fast  ✔
    working    Claude is generating (repeat every 1.2 s)    high distant shimmer, tremolo     ✔
    done       animation lands on the wall, right now       one struck-glass note             ✔
    unheard    didn't catch that / wake word, no speech     (placeholder, falling pair)
    error      generation failed / validation rejected      (placeholder, buzz)

All in one family: A-minor add9 pads, slow attacks, detuned voices, a short room.

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


SOFT_DEFAULT = (1.0, 0.25, 0.08)


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


def _reverb(x: np.ndarray, ms: float = 260, mix: float = 0.4) -> np.ndarray:
    """Cheap room: convolve with a short exponentially decaying noise burst."""
    n = int(RATE * ms / 1000)
    rng = np.random.default_rng(7)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4))
    ir[0] = 0
    ir /= np.abs(ir).sum() / 3
    wet = np.convolve(x, ir)
    dry = np.concatenate([x, np.zeros(len(wet) - len(x))])
    out = (1 - mix) * dry + mix * wet
    return out / max(1e-9, np.abs(out).max()) * np.abs(x).max()


def _pad(freqs, ms: float, *, attack=0.06, decay=0.25, detune=0.004, drift=1.0, curve=1.0) -> np.ndarray:
    """Soft chord: each note doubled and detuned, slow attack, optional pitch drift (ratio over length).
    curve>1 pushes the drift toward the end (question-like lift)."""
    n = int(RATE * ms / 1000)
    t = np.arange(n) / RATE
    x = np.zeros(n)
    for f in freqs:
        for d in (1 - detune, 1 + detune):
            freq = f * d * drift ** ((t / t[-1]) ** curve)
            phase = 2 * np.pi * np.cumsum(freq) / RATE
            x += np.sin(phase) + 0.15 * np.sin(2 * phase)
    x /= np.abs(x).max()
    env = (1 - np.exp(-t / attack)) * np.exp(-t / decay)
    r = min(n, int(RATE * 0.02))
    env[-r:] *= np.linspace(1, 0, r)
    return x * env


def _bloom(ms: float, *, attack: float, decay: float, open_at: float, open_len: float,
           rev_ms: float, rev_mix: float, bright=0.55, chord=(220, 261.63, 329.63, 493.88)) -> np.ndarray:
    """The 'listening' cue: minor add9 pad that brightens late (octave-up copy fades in). No pitch movement."""
    base = _pad(chord, ms, attack=attack, decay=decay, detune=0.008)
    hi = _pad(tuple(f * 2 for f in chord), ms, attack=attack, decay=decay, detune=0.008)
    t = np.arange(len(base)) / RATE
    late = np.clip((t - open_at) / open_len, 0, 1) ** 2
    return _reverb((base + bright * hi * late) / (1 + bright * 0.6), ms=rev_ms, mix=rev_mix)


def _breath(ms: float, lo: float, hi: float, *, attack=0.08, decay=0.15, seed=3) -> np.ndarray:
    """Band-limited noise swell — an intake of breath."""
    n = int(RATE * ms / 1000)
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    spec *= np.exp(-((np.log(np.maximum(f, 1)) - np.log(np.sqrt(lo * hi))) ** 2) / (2 * (np.log(hi / lo) / 4) ** 2))
    x = np.fft.irfft(spec, n); x /= np.abs(x).max()
    t = np.arange(n) / RATE
    env = (1 - np.exp(-t / attack)) * np.exp(-t / decay)
    return x * env / max(1e-9, env.max())


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
        # You stopped talking. The bloom inverted: bright chord that closes down fast — turning inward.
        hi = _pad(tuple(f * 2 for f in (220, 261.63, 329.63, 493.88)), 420, attack=0.03, decay=0.12, detune=0.008)
        lo = _pad((220, 261.63, 329.63, 493.88), 420, attack=0.10, decay=0.16, detune=0.008)
        return _reverb((hi + 0.7 * lo) / 1.7, ms=650, mix=0.5)
    if name == "listening":
        # Wake word heard. Wall glows blue and shimmers; this swells with it.
        # Minor add9 pad, slow attack, no pitch movement; an octave-up shimmer
        # opens over the last stretch — the "?" comes from brightening, not pitch.
        # Chosen 2026-09-04 after auditioning ~20 candidates.
        return _bloom(1200, attack=0.45, decay=0.45, open_at=0.55, open_len=0.35, rev_ms=1100, rev_mix=0.6)
    if name == "working":
        # Claude is generating. Play every WORKING_PERIOD seconds: a high distant shimmer,
        # two detuned octave voices with a slow tremolo. The wall's shimmer breathes to the same period.
        x = _pad((987.77, 1318.5), 900, attack=0.25, decay=0.3, detune=0.012)
        t = np.arange(len(x)) / RATE
        return _reverb(x * (0.7 + 0.3 * np.sin(2 * np.pi * 3.2 * t)) * 0.6, ms=600, mix=0.55)
    if name == "done":
        # Animation lands on the wall at this exact moment. One clear high note, like struck glass,
        # over a faint echo of the chord.
        top = _pad((880, 1760), 500, attack=0.005, decay=0.16, detune=0.004)
        lo = _pad((220, 261.63, 329.63, 493.88), 500, attack=0.02, decay=0.2, detune=0.008) * 0.35
        return _reverb(_mix(top, lo) * 1.5, ms=800, mix=0.5)
    if name == "unheard":
        return _seq(_tone(880, 120, harmonics=SOFT, decay=0.08),
                    _tone(660, 200, harmonics=SOFT, decay=0.12), gap_ms=20)
    if name == "error":
        buzz = _mix(_tone(220, 240, harmonics=(1.0, 0, 0.33, 0, 0.2), decay=0.4),
                    _tone(233, 240, harmonics=(1.0, 0, 0.33, 0, 0.2), decay=0.4))
        return _seq(buzz, buzz, gap_ms=60)
    raise KeyError(name)


NAMES = ("listening", "heard", "working", "done", "unheard", "error")
WORKING_PERIOD = 1.2  # seconds between "working" pulses; the wall shimmer breathes to this


def path(name: str) -> Path:
    return CACHE / f"{name}.wav"


def render(name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    x = synth(name)
    x = x / max(1e-9, np.abs(x).max()) * 0.9 * GAIN   # consistent peak across cues
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
    if not path(name).exists():
        render(name)
    p = subprocess.Popen(["aplay", "-q", "-D", SPEAKER, str(path(name))],
                         stdout=subprocess.DEVNULL)
    if block:
        p.wait()
        return None
    return p


def main(argv: list[str]) -> None:
    for n in NAMES:
        render(n)
    names = argv or list(NAMES)
    for n in names:
        if n.startswith("pause:"):
            time.sleep(float(n.split(":")[1])); continue
        print(n, flush=True)
        play(n, block=False)          # non-blocking so sequences overlap like the real thing
        time.sleep(float(os.environ.get("LEDFRAME_EARCON_GAP", "1.2")))


if __name__ == "__main__":
    main(sys.argv[1:])
