from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
import requests

JSON_URL = "http://141.164.53.195/live/korea-live.json"

OUTPUT1 = "Aniplus2.m3u8"   # DIYP
OUTPUT2 = "Aniplus.m3u8"    # OTT/IPTV nested HLS 720p + audio

TARGET_NAME = "애니플러스"

# Pilihan kualitas:
# stream1 = 1080p
# stream2 = 900p
# stream3 = 720p
# stream4 = 540p
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


def extract_m3u8_only(uris):
    """Ambil URL .m3u8 pertama untuk OUTPUT1."""

    def is_m3u8(u):
        return (
            isinstance(u, str)
            and ".m3u8" in u.lower()
            and not is_blocked_url(u)
        )

    if isinstance(uris, list):
        for u in uris:
            if is_m3u8(u):
                return u.strip()

    elif isinstance(uris, dict):
        for u in uris.values():
            if is_m3u8(u):
                return u.strip()

    elif isinstance(uris, str):
        if is_m3u8(uris):
            return uris.strip()

    return None


def extract_m3u8_or_php(uris):
    """
    Prioritas .m3u8.
    Fallback .php.
    """

    urls = []

    def is_valid(u):
        return (
            isinstance(u, str)
            and (
                ".m3u8" in u.lower()
                or u.lower().endswith(".php")
            )
            and not is_blocked_url(u)
        )

    if isinstance(uris, list):
        urls = [u.strip() for u in uris if is_valid(u)]

    elif isinstance(uris, dict):
        urls = [u.strip() for u in uris.values() if is_valid(u)]

    elif isinstance(uris, str):
        if is_valid(uris):
            urls = [uris.strip()]

    for u in urls:
        if ".m3u8" in u.lower():
            return u

    if urls:
        return urls[0]

    return None


def build_absolute_hls_720(master_url):
    """
    Dari URL seperti:
    https://domain/path/playlist.m3u8?token=xxx

    Dibuat menjadi:
    audio = https://domain/path/vc1_audio_ko_ko.m3u8?token=xxx
    video = https://domain/path/vc1_video_stream3.m3u8?token=xxx
    """

    if not master_url or ".m3u8" not in master_url.lower():
        return None

    parts = urlsplit(master_url)

    # Ambil folder base dari playlist.m3u8 / stream m3u8
    base_path = parts.path.rsplit("/", 1)[0] + "/"

    # Pertahankan query token penuh
    query = parts.query

    audio_url = urlunsplit((
        parts.scheme,
        parts.netloc,
        base_path + AUDIO_FILE,
        query,
        ""
    ))

    video_url = urlunsplit((
        parts.scheme,
        parts.netloc,
        base_path + VIDEO_FILE,
        query,
        ""
    ))

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
        video_url
    ]


def run():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(
            JSON_URL,
            headers=headers,
            timeout=20
        )

        r.raise_for_status()
        data = r.json()

    except Exception as e:
        print(f"{datetime.now()} 获取 JSON 失败: {e}")
        return

    lines1 = ["#EXTM3U"]
    lines2 = None

    count1 = 0
    count2 = 0

    for item in data:
        name = item.get("name", "").strip()
        uris = item.get("uris")

        if name != TARGET_NAME:
            continue

        # OUTPUT1 DIYP
        url1 = extract_m3u8_only(uris)
        if url1:
            lines1.append(f"{name},{url1}")
            count1 += 1

        # OUTPUT2 HLS 720p + audio
        master_url = extract_m3u8_or_php(uris)
        if master_url:
            built = build_absolute_hls_720(master_url)
            if built:
                lines2 = built
                count2 = 1
                break

    if lines2 is None:
        lines2 = [
            "#EXTM3U",
            "# ERROR: URL m3u8 target tidak ditemukan"
        ]

    with open(OUTPUT1, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines1) + "\n")

    with open(OUTPUT2, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines2) + "\n")

    print(f"{datetime.now()} DIYP 频道数量: {count1}")
    print(f"{datetime.now()} IPTV 频道数量: {count2}")
    print(f"{datetime.now()} 已生成文件: {OUTPUT1}, {OUTPUT2}")


if __name__ == "__main__":
    run()
