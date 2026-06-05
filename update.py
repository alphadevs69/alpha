from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
import requests

JSON_URL = "http://141.164.53.195/live/korea-live.json"

# =========================
# TARGET CHANNELS
# =========================
TARGETS = [
    {
        "name": "애니플러스",
        "output": "Aniplus.m3u8"
    },
    {
        "name": "ANIBOX",
        "output": "Anibox.m3u8"
    },
    {
        "name": "JTBC",
        "output": "JTBC.m3u8"
    }
]

# =========================
# QUALITY
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


def extract_m3u8_or_php(uris):

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

    if not master_url or ".m3u8" not in master_url.lower():
        return None

    parts = urlsplit(master_url)

    base_path = parts.path.rsplit("/", 1)[0] + "/"

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

    for target in TARGETS:

        target_name = target["name"]
        output = target["output"]

        lines = None
        count = 0

        for item in data:

            name = item.get("name", "").strip()
            uris = item.get("uris")

            if name != target_name:
                continue

            master_url = extract_m3u8_or_php(uris)

            if master_url:

                built = build_absolute_hls_720(master_url)

                if built:
                    lines = built
                    count = 1
                    break

        if lines is None:

            lines = [
                "#EXTM3U",
                "# ERROR: URL m3u8 target tidak ditemukan"
            ]

        with open(output, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")

        print(f"{datetime.now()} {target_name}")
        print(f"IPTV: {count}")
        print(f"生成文件: {output}")
        print("-" * 50)


if __name__ == "__main__":
    run()