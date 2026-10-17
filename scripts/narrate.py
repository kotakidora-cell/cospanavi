# YouTube Short用の日本語ナレーション(VOICEVOX)＋BGMダッキング合成。
# VOICEVOXエンジン(http://127.0.0.1:50021)が起動していれば利用、無ければ呼び出し側でBGMのみにフォールバック。
# 使い方(各Short生成器から): import narrate; narrate.build_narrated_video(pngs, texts, out, bgm=bgm)
import os, json, wave, tempfile, subprocess, urllib.request, urllib.parse
import imageio_ffmpeg

HOST = "http://127.0.0.1:50021"
SPEAKER = int(os.environ.get("VV_SPEAKER", "3"))   # 3=ずんだもん(ノーマル)。2=四国めたん, 8=春日部つむぎ 等
SPEED = float(os.environ.get("VV_SPEED", "1.05"))  # 少し速めでテンポ良く
BGM_VOL = float(os.environ.get("BGM_VOL", "0.08"))  # BGM音量(ナレーションに対して大幅に下げる。0.0〜1.0)
NARR_VOL = float(os.environ.get("NARR_VOL", "2.5"))  # ナレーション増幅(VOICEVOX出力は小さめなので持ち上げる。リミッターで歪み防止)
PAD = 0.45      # 各ナレーション末尾の余白(秒)
MIN_DUR = 2.0   # 1シーンの最短表示(秒)
FF = imageio_ffmpeg.get_ffmpeg_exe()


def available():
    try:
        urllib.request.urlopen(HOST + "/version", timeout=3).read()
        return True
    except Exception:
        return False


def _post(path, data=None, is_json=False):
    headers = {"Content-Type": "application/json"} if is_json else {}
    req = urllib.request.Request(HOST + path, data=data, headers=headers, method="POST")
    return urllib.request.urlopen(req, timeout=120).read()


def synth(text, path, speaker=None, speed=None):
    speaker = SPEAKER if speaker is None else speaker
    speed = SPEED if speed is None else speed
    q = json.loads(_post("/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": speaker})))
    q["speedScale"] = speed
    wav = _post("/synthesis?" + urllib.parse.urlencode({"speaker": speaker}),
                data=json.dumps(q).encode("utf-8"), is_json=True)
    open(path, "wb").write(wav)


def _dur(p):
    with wave.open(p, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        print(r.stdout.decode("utf-8", "replace")[-1500:])
        raise SystemExit("ffmpeg失敗")


def build_narrated_video(pngs, texts, out, bgm=None, speaker=None, bgm_vol=None):
    """各シーンPNGにナレーションを割り当て、ナレーション長に合わせて表示時間を決定。BGMは音量を下げて重ねる。"""
    bgm_vol = BGM_VOL if bgm_vol is None else bgm_vol
    tmp = tempfile.mkdtemp()
    durs, apads = [], []
    for i, (png, txt) in enumerate(zip(pngs, texts)):
        w = os.path.join(tmp, f"n{i}.wav")
        synth(txt, w, speaker)
        sd = max(MIN_DUR, _dur(w) + PAD)
        durs.append(sd)
        ap = os.path.join(tmp, f"a{i}.wav")
        _run([FF, "-y", "-i", w, "-af", f"apad=whole_dur={sd:.3f}", "-ar", "44100", "-ac", "2", ap])
        apads.append(ap)
    total = sum(durs)
    # 映像: 画像をdurで並べる(ハードカット=ナレーションと同期)
    vlst = os.path.join(tmp, "v.txt")
    with open(vlst, "w", encoding="utf-8") as f:
        for png, sd in zip(pngs, durs):
            f.write(f"file '{png.replace(os.sep, '/')}'\nduration {sd:.3f}\n")
        f.write(f"file '{pngs[-1].replace(os.sep, '/')}'\n")
    vid = os.path.join(tmp, "v.mp4")
    _run([FF, "-y", "-f", "concat", "-safe", "0", "-i", vlst,
          "-vf", "scale=1080:1920,fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20", vid])
    # ナレーション連結(各シーン長に合わせてパディング済み)
    alst = os.path.join(tmp, "a.txt")
    with open(alst, "w", encoding="utf-8") as f:
        for ap in apads:
            f.write(f"file '{ap.replace(os.sep, '/')}'\n")
    narr = os.path.join(tmp, "narr.wav")
    _run([FF, "-y", "-f", "concat", "-safe", "0", "-i", alst, "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", narr])
    # ミックス: ナレーション + 音量を下げたBGM
    if bgm and os.path.exists(bgm):
        # ナレーションを増幅＋BGMを大幅に下げ、amixの自動正規化を切って(normalize=0)声を主役に。最後にリミッターで歪み防止。
        _run([FF, "-y", "-i", vid, "-i", narr, "-stream_loop", "-1", "-i", bgm,
              "-filter_complex",
              f"[1:a]volume={NARR_VOL}[v];[2:a]volume={bgm_vol}[bg];"
              f"[v][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mx];[mx]alimiter=limit=0.95[a]",
              "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])
    else:
        _run([FF, "-y", "-i", vid, "-i", narr, "-filter_complex", f"[1:a]volume={NARR_VOL}[a]",
              "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])
    return total
