from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
import requests

# Source list channel KR
M3U_URL = "https://gitflic.ru/project/reaperc/kr-tv/blob/raw?file=KR_Categories.m3u"

# =========================
# TARGET CHANNELS
# =========================
TARGETS = [
    {"name": "Aniplus", "aliases": ["Aniplus", "애니플러스"], "output": "Aniplus.m3u8"},
    {"name": "ANIBOX", "aliases": ["ANIBOX", "애니박스"], "output": "Anibox.m3u8"},
    {"name": "JTBC", "aliases": ["JTBC"], "output": "JTBC.m3u8"},
]

# =========================
# QUALITY 720 TVING
# =========================
VIDEO_FILE = "vc1_video_stream3.m3u8"
AUDIO_FILE = "vc1_audio_ko_ko.m3u8"

VIDEO_BANDWIDTH = 2192000
VIDEO_RESOLUTION = "1280x720"
VIDEO_CODECS = "avc1.64001f,mp4a.40.2"


def is_blocked_url(u):
    u = (u or "").lower()
    return (
        "wavve" in u
        or "file-1253962976.cos" in u
    )


def is_valid_url(u):
    u_low = (u or "").lower().strip()
    return (
        isinstance(u, str)
        and (".m3u8" in u_low or u_low.endswith(".php") or "#.m3u8" in u_low)
        and not is_blocked_url(u_low)
    )


def parse_attr(extinf, key):
    marker = key + '="'
    if marker not in extinf:
        return ""
    return extinf.split(marker, 1)[1].split('"', 1)[0].strip()


def parse_m3u(text):
    """Return list: {name, tvg_name, tvg_id, extinf, url}"""
    channels = []
    last_extinf = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            last_extinf = line
            continue

        if last_extinf and not line.startswith("#"):
            name = last_extinf.rsplit(",", 1)[-1].strip() if "," in last_extinf else ""
            channels.append({
                "name": name,
                "tvg_name": parse_attr(last_extinf, "tvg-name"),
                "tvg_id": parse_attr(last_extinf, "tvg-id"),
                "extinf": last_extinf,
                "url": line,
            })
            last_extinf = None

    return channels


def find_channel(channels, aliases):
    aliases_low = [a.lower().strip() for a in aliases]

    for ch in channels:
        fields = [ch.get("name", ""), ch.get("tvg_name", ""), ch.get("tvg_id", "")]
        fields_low = [f.lower().strip() for f in fields]

        # exact match first
        if any(a == f for a in aliases_low for f in fields_low):
            return ch

    for ch in channels:
        fields = [ch.get("name", ""), ch.get("tvg_name", ""), ch.get("tvg_id", "")]
        text = " ".join(fields).lower()

        # contains match fallback
        if any(a and a in text for a in aliases_low):
            return ch

    return None


def normalize_tving_to_720(master_url):
    """Build 720p HLS with audio+video when source is TVING O2."""
    if not master_url or ".m3u8" not in master_url.lower():
        return None

    if "tving-live-o2" not in master_url.lower():
        return None

    parts = urlsplit(master_url)
    base_path = parts.path.rsplit("/", 1)[0] + "/"
    query = parts.query

    audio_url = urlunsplit((parts.scheme, parts.netloc, base_path + AUDIO_FILE, query, ""))
    video_url = urlunsplit((parts.scheme, parts.netloc, base_path + VIDEO_FILE, query, ""))

    return [
        "#EXTM3U",
        "#EXT-X-VERSION:4",
        "#EXT-X-INDEPENDENT-SEGMENTS",
        "",
        (
            '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio_0",NAME="Korean",'
            'DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="ko",'
            f'URI="{audio_url}"'
        ),
        "",
        (
            f'#EXT-X-STREAM-INF:BANDWIDTH={VIDEO_BANDWIDTH},'
            f'CODECS="{VIDEO_CODECS}",'
            f'RESOLUTION={VIDEO_RESOLUTION},AUDIO="audio_0"'
        ),
        video_url,
    ]


def build_output(url):
    if not is_valid_url(url):
        return None

    tving_720 = normalize_tving_to_720(url)
    if tving_720:
        return tving_720

    return ["#EXTM3U", url]


def run():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(M3U_URL, headers=headers, timeout=30)
        r.raise_for_status()
        channels = parse_m3u(r.text)
    except Exception as e:
        print(f"{datetime.now()} gagal ambil M3U: {e}")
        return

    for target in TARGETS:
        output = target["output"]
        ch = find_channel(channels, target["aliases"])

        lines = None
        count = 0

        if ch:
            lines = build_output(ch.get("url"))
            if lines:
                count = 1

        if lines is None:
            lines = [
                "#EXTM3U",
                f"# ERROR: URL target tidak ditemukan untuk {target['name']}",
            ]

        with open(output, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")

        print(f"{datetime.now()} {target['name']}")
        print(f"IPTV: {count}")
        print(f"生成文件: {output}")
        print("-" * 50)


if __name__ == "__main__":
    run()
