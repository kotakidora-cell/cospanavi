# 著作権フリーの自作POP BGMを生成 → shorts/bgm.mp3
# I-V-vi-IV(C-G-Am-F)進行 + きらきらアルペジオ + 4つ打ちキック。約26秒。
import numpy as np, os, wave, subprocess
import imageio_ffmpeg

SR = 44100
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "shorts"); os.makedirs(OUT, exist_ok=True)

def tone(freq, dur, kind="pluck", amp=0.3):
    n = int(SR * dur); t = np.arange(n) / SR
    if kind == "kick":
        f = 110 * np.exp(-t * 25) + 45          # ピッチが落ちるキック
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR); env = np.exp(-t * 11)
    elif kind == "bass":
        sig = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * 2 * freq * t)
        env = np.minimum(1, t * 40) * np.exp(-t * 2.2)
    elif kind == "pad":
        sig = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
        env = np.minimum(1, t * 6) * np.exp(-t * 0.7)
    else:  # pluck(きらきら)
        sig = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t)
        env = np.exp(-t * 6.5)
    return (sig * env * amp).astype(np.float32)

bpm = 128; beat = 60 / bpm; bar = beat * 4
# (名前, 三和音[中音域], ベース根音)
prog = [("C",  [261.63, 329.63, 392.00], 130.81),
        ("G",  [196.00, 246.94, 293.66], 98.00),
        ("Am", [220.00, 261.63, 329.63], 110.00),
        ("F",  [174.61, 220.00, 261.63], 87.31)]
loops = 4
buf = np.zeros(int(SR * bar * len(prog) * loops) + SR, dtype=np.float32)

def add(sig, at):
    i = int(SR * at); j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]

pos = 0.0
for _ in range(loops):
    for name, triad, bass in prog:
        add(tone(bass, bar * 0.98, "bass", 0.32), pos)
        for f in triad:
            add(tone(f, bar * 0.98, "pad", 0.05), pos)         # 薄いパッド
        for b in range(4):
            add(tone(0, 0.2, "kick", 0.7), pos + b * beat)     # 4つ打ち
        arp = [triad[0], triad[1], triad[2], triad[1], triad[0], triad[1], triad[2], triad[1]]
        for k, f in enumerate(arp):
            add(tone(f * 2, beat / 2 * 0.95, "pluck", 0.2), pos + k * (beat / 2))  # 1oct上できらきら
        pos += bar

buf = buf[: int(SR * (bar * len(prog) * loops))]
# フェード
fi = int(SR * 0.3); fo = int(SR * 1.6)
buf[:fi] *= np.linspace(0, 1, fi); buf[-fo:] *= np.linspace(1, 0, fo)
buf /= (np.max(np.abs(buf)) + 1e-6); buf *= 0.89   # ノーマライズ
i16 = (buf * 32767).astype(np.int16)
stereo = np.repeat(i16[:, None], 2, axis=1)  # ステレオ

wav = os.path.join(OUT, "bgm.wav")
with wave.open(wav, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(stereo.tobytes())
mp3 = os.path.join(OUT, "bgm.mp3")
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", wav, "-b:a", "160k", mp3],
               check=True, capture_output=True)
os.remove(wav)
print(f"生成: {mp3}  ({len(buf)/SR:.1f}秒, C-G-Am-F POP)")
