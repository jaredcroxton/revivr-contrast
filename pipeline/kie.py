#!/usr/bin/env python3
"""
kie.py - KIE-engine chain runner for the CREW Foundry scroll-film (mechanical lane).

Implements the scroll-film-studio chain contract on kie.ai REST:
  keyframe : google/nano-banana opening still -> assets/K0.png (+ hosted url cache)
  chain    : clip N seeds from the ffmpeg-extracted LITERAL last frame of clip N-1
             (uploaded via the KIE base64 file endpoint), junction SSIM-gated.

  create : POST https://api.kie.ai/api/v1/jobs/createTask {model, input} -> data.taskId
  poll   : GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...     -> data.state, data.resultJson
  upload : POST https://kieai.redpandaai.co/api/file-base64-upload       -> data.downloadUrl
  credit : GET  https://api.kie.ai/api/v1/chat/credit                    -> data (float)

Usage:
  python3 pipeline/kie.py balance
  python3 pipeline/kie.py keyframe
  python3 pipeline/kie.py chain          # full run: keyframe (if missing) then clip1..clip5
"""
import base64, json, os, re, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOLUTION = os.environ.get("KIE_RES", "480p")
CLIPS = os.path.join(ROOT, "assets", "clips-" + RESOLUTION)
TMP = os.path.join(ROOT, ".tmp")
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
POLL_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
UPLOAD_URL = "https://kieai.redpandaai.co/api/file-base64-upload"
CREDIT_URL = "https://api.kie.ai/api/v1/chat/credit"
IMG_MODEL = "google/nano-banana"
EDIT_MODEL = "bytedance/seedream-v4-edit"
VID_MODEL = os.environ.get("KIE_MODEL", "bytedance/v1-pro-image-to-video")
DURATION = "5"
POLL_INTERVAL = 6
POLL_TIMEOUT = 900
UA = "Mozilla/5.0"

PLAN = json.load(open(os.path.join(ROOT, "pipeline", "storyboard.json")))


def load_key():
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        p = os.path.join(ROOT, ".env")
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("KIE_API_KEY=") and not line.startswith("#"):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("ERROR: KIE_API_KEY not set (put it in .env)")
    return key


def _post(url, payload, key):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s from %s: %s" % (e.code, url, e.read().decode("utf-8", "ignore")[:400]))


def _get(url, key):
    req = urllib.request.Request(url, method="GET", headers={"Authorization": "Bearer " + key, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def balance(key):
    res = _get(CREDIT_URL, key)
    return float(res.get("data", -1))


def upload(path, key):
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    res = _post(UPLOAD_URL, {"base64Data": "data:%s;base64,%s" % (mime, b64),
                             "uploadPath": "revivr-contrast", "fileName": os.path.basename(path)}, key)
    url = (res.get("data") or {}).get("downloadUrl") or (res.get("data") or {}).get("fileUrl")
    if not url:
        raise RuntimeError("upload failed: " + json.dumps(res)[:300])
    print("  uploaded -> %s" % url, flush=True)
    return url


def create_task(model, inp, key):
    res = _post(CREATE_URL, {"model": model, "input": inp}, key)
    if res.get("code") != 200:
        raise RuntimeError("createTask error: " + json.dumps(res)[:400])
    tid = (res.get("data") or {}).get("taskId")
    if not tid:
        raise RuntimeError("no taskId: " + json.dumps(res)[:300])
    return tid


def poll(tid, key):
    start = time.time()
    while True:
        if time.time() - start > POLL_TIMEOUT:
            raise RuntimeError("poll timeout for task " + tid)
        res = _get(POLL_URL + "?taskId=" + tid, key)
        d = res.get("data") or {}
        state = d.get("state", "")
        if state == "success":
            rj = json.loads(d.get("resultJson") or "{}")
            urls = (rj.get("resultUrls") or [])
            if not urls:
                raise RuntimeError("success but no resultUrls: " + json.dumps(rj)[:300])
            return urls[0]
        if state == "fail":
            raise RuntimeError("task failed: " + json.dumps(d)[:400])
        time.sleep(POLL_INTERVAL)


def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    print("  saved %s (%.1f MB)" % (dest, os.path.getsize(dest) / 1048576), flush=True)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + list(args), check=True)


def extract_ends(mp4, name):
    first = os.path.join(CLIPS, name + "-first.png")
    last = os.path.join(CLIPS, name + "-last.png")
    ffmpeg("-i", mp4, "-vf", "select=eq(n\\,0)", "-frames:v", "1", "-update", "1", "-q:v", "1", first)
    ffmpeg("-sseof", "-0.05", "-i", mp4, "-update", "1", "-q:v", "1", last)
    return first, last


def ssim(a, b):
    out = subprocess.run(["ffmpeg", "-i", a, "-i", b, "-lavfi",
                          "[1:v][0:v]scale2ref=flags=bicubic[b][a];[a][b]ssim", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"All:([0-9.]+)", out)
    return float(m.group(1)) if m else -1.0


def do_keyframe(key):
    dest = os.path.join(ROOT, "assets", "keyframes", "K0.png")
    cache = os.path.join(TMP, "k0_url.json")
    if os.path.exists(dest) and os.path.exists(cache):
        print("[K0] exists, skip", flush=True)
        return json.load(open(cache))["url"]
    print("[K0] nano-banana keyframe...", flush=True)
    tid = create_task(IMG_MODEL, {"prompt": PLAN["keyframe"], "output_format": "png",
                                  "aspect_ratio": "16:9"}, key)
    url = poll(tid, key)
    download(url, dest)
    os.makedirs(TMP, exist_ok=True)
    json.dump({"url": url}, open(cache, "w"))
    return url


def seedream_edit(prompt, image_urls, key, dest, size="2K", model=None):
    """Edit an image (seedream-v4-edit or nano-banana-edit); param fallbacks discovered live."""
    global EDIT_MODEL
    if model:
        EDIT_MODEL = model
    if EDIT_MODEL == "google/nano-banana-edit":
        variants = [
            {"prompt": prompt, "image_urls": image_urls, "output_format": "png"},
            {"prompt": prompt, "image_urls": image_urls},
        ]
    else:
        variants = [
        {"prompt": prompt, "image_urls": image_urls, "image_size": "landscape_16_9", "output_format": "png"},
        {"prompt": prompt, "image_urls": image_urls, "image_size": "16:9", "output_format": "png"},
        {"prompt": prompt, "image_urls": image_urls, "image_size": "1920x1080", "output_format": "png"},
        {"prompt": prompt, "image_urls": image_urls, "aspect_ratio": "16:9", "output_format": "png"},
        {"prompt": prompt, "image_urls": image_urls},
        ]
    last_err = None
    for inp in variants:
        try:
            tid = create_task(EDIT_MODEL, inp, key)
            url = poll(tid, key)
            download(url, dest)
            return url
        except Exception as e:
            last_err = e
            print("  [edit] variant failed: %s" % str(e)[:200], flush=True)
    raise RuntimeError("seedream edit failed all variants: %s" % last_err)


def dims(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                          "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def match_aspect(img, ref):
    """Center-crop img in place to ref's aspect ratio (edit models ignore aspect params)."""
    iw, ih = dims(img)
    rw, rh = dims(ref)
    if abs(iw / ih - rw / rh) < 0.01:
        return
    if iw / ih > rw / rh:
        cw, ch = int(ih * rw / rh), ih
    else:
        cw, ch = iw, int(iw * rh / rw)
    tmp = img + ".crop.png"
    ffmpeg("-i", img, "-vf", "crop=%d:%d" % (cw, ch), tmp)
    os.replace(tmp, img)
    print("  aspect-matched %s -> %dx%d" % (os.path.basename(img), cw, ch), flush=True)


def do_inject(name, prev_last, inject, key):
    """Replace the chain seed with an edited version of the literal last frame."""
    seed_png = os.path.join(CLIPS, name + "-seed.png")
    if not os.path.exists(seed_png):
        print("[%s] inject: %s edit of previous last frame" % (name, inject.get("model", EDIT_MODEL)), flush=True)
        urls = [upload(prev_last, key)]
        if inject.get("ref"):
            urls.append(upload(os.path.join(ROOT, inject["ref"]), key))
        seedream_edit(inject["edit_prompt"], urls, key, seed_png, model=inject.get("model"))
    match_aspect(seed_png, prev_last)
    drift = ssim(prev_last, seed_png)
    print("[%s] INJECT-DRIFT SSIM %.4f (raw last frame vs edited seed)" % (name, drift), flush=True)
    return seed_png


def internal_cut_scan(mp4, name):
    """SSIM consecutive sampled frames inside a clip; a mid-clip teleport shows as a low pair."""
    scan = os.path.join(TMP, name + "-scan")
    os.makedirs(scan, exist_ok=True)
    for f in os.listdir(scan):
        os.remove(os.path.join(scan, f))
    ffmpeg("-i", mp4, "-vf", "select='not(mod(n\\,12))',scale=432:-2", "-vsync", "vfr",
           os.path.join(scan, "s_%03d.png"))
    frames = sorted(os.listdir(scan))
    worst, worst_at = 1.0, -1
    for i in range(len(frames) - 1):
        s = ssim(os.path.join(scan, frames[i]), os.path.join(scan, frames[i + 1]))
        if 0 <= s < worst:
            worst, worst_at = s, i
    verdict = "OK" if worst >= 0.5 else "INTERNAL-CUT?"
    print("[%s] internal-scan worst consecutive SSIM %.3f at sample %d -> %s"
          % (name, worst, worst_at, verdict), flush=True)


def do_extras(key):
    b0 = balance(key)
    for x in PLAN.get("extras", []):
        name = x["id"]
        res = x.get("resolution", RESOLUTION)
        dest = os.path.join(ROOT, "assets", "clips-extra", name + ".mp4")
        if os.path.exists(dest) and os.path.getsize(dest) > 100000:
            print("[%s] exists, skip" % name, flush=True)
            continue
        seed_png = os.path.join(ROOT, "assets", "keyframes", name + "-seed.png")
        if "seed_edit" in x:
            if not os.path.exists(seed_png):
                print("[%s] seed edit from %s" % (name, x["seed_edit"]["ref"]), flush=True)
                ref_url = upload(os.path.join(ROOT, x["seed_edit"]["ref"]), key)
                seedream_edit(x["seed_edit"]["prompt"], [ref_url], key, seed_png)
            seed_url = upload(seed_png, key)
        else:
            seed_url = upload(os.path.join(ROOT, x["seed_image"]), key)
        for attempt in range(1, 5):
            print("[%s] create (%s %s/%ss) attempt %d" % (name, VID_MODEL, res, DURATION, attempt), flush=True)
            try:
                tid = create_task(VID_MODEL, {"prompt": x["prompt"], "image_url": seed_url,
                                              "resolution": res, "duration": DURATION,
                                              "camera_fixed": False}, key)
                url = poll(tid, key)
                download(url, dest)
                break
            except Exception as e:
                print("  [%s] error: %s" % (name, str(e)[:300]), flush=True)
                if attempt == 4:
                    raise
                time.sleep(12)
    b1 = balance(key)
    print("extras balance delta: %.1f credits" % (b0 - b1), flush=True)


def gen_clip(name, seed_url, prompt, prev_last, key):
    dest = os.path.join(CLIPS, name + ".mp4")
    if os.path.exists(dest) and os.path.getsize(dest) > 100000:
        print("[%s] exists, skip generation" % name, flush=True)
    else:
        for attempt in range(1, 5):
            print("[%s] create (%s %s/%ss) attempt %d" % (name, VID_MODEL, RESOLUTION, DURATION, attempt), flush=True)
            try:
                tid = create_task(VID_MODEL, {"prompt": prompt, "image_url": seed_url,
                                              "resolution": RESOLUTION, "duration": DURATION,
                                              "camera_fixed": False}, key)
                url = poll(tid, key)
                download(url, dest)
                break
            except Exception as e:
                print("  [%s] error: %s" % (name, str(e)[:300]), flush=True)
                if attempt == 4:
                    raise
                time.sleep(12)
    first, last = extract_ends(dest, name)
    internal_cut_scan(dest, name)
    if prev_last:
        s = ssim(prev_last, first)
        compare = os.path.join(CLIPS, name + "-junction.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", prev_last, "-i", first,
                        "-filter_complex", "[1:v][0:v]scale2ref=flags=bicubic[b][a];[a][b]hstack", compare])
        verdict = "PASS" if s >= 0.88 else ("REVIEW" if s >= 0.80 else "INSPECT")
        print("[%s] JUNCTION SSIM %.4f %s (side-by-side: %s)" % (name, s, verdict, compare), flush=True)
    return last


def do_chain(key):
    b0 = balance(key)
    print("balance before: %.1f  (model %s, res %s)" % (b0, VID_MODEL, RESOLUTION), flush=True)
    k0_url = do_keyframe(key)
    seed_url, prev_last = k0_url, None
    for clip in PLAN["clips"]:
        name = clip["id"]
        if prev_last and clip.get("inject"):
            seed_png = do_inject(name, prev_last, clip["inject"], key)
            seed_url = upload(seed_png, key)
            prev_last = seed_png
        last = gen_clip(name, seed_url, clip["prompt"], prev_last, key)
        prev_last = last
        if clip is not PLAN["clips"][-1] and not PLAN["clips"][PLAN["clips"].index(clip) + 1].get("inject"):
            print("[%s] uploading last frame for next seed..." % name, flush=True)
            seed_url = upload(last, key)
    b1 = balance(key)
    print("balance after: %.1f  (spent %.1f credits)" % (b1, b0 - b1), flush=True)
    print("CHAIN DONE", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "chain"
    k = load_key()
    if cmd == "balance":
        print(balance(k))
    elif cmd == "keyframe":
        do_keyframe(k)
    elif cmd == "chain":
        do_chain(k)
    elif cmd == "extras":
        do_extras(k)
    else:
        sys.exit("usage: kie.py balance|keyframe|chain|extras")
