from datetime import datetime
import requests

JSON_URL = "http://141.164.53.195/live/korea-live.json"

OUTPUT1 = "Aniplus2.m3u8"   # DIYP
OUTPUT2 = "Aniplus.m3u8"    # IPTV

TARGET_NAME = "애니플러스"


def extract_m3u8_only(uris):
    """Hanya ambil m3u8 untuk OUTPUT1"""

    def is_m3u8(u):
        return (
            isinstance(u, str)
            and ".m3u8" in u.lower()
            and "wavve" not in u.lower()
            and "file-1253962976.cos" not in u.lower()
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
    Prioritas m3u8
    fallback php
    """

    urls = []

    def is_valid(u):
        return (
            isinstance(u, str)
            and (
                ".m3u8" in u.lower()
                or u.lower().endswith(".php")
            )
            and "wavve" not in u.lower()
            and "file-1253962976.cos" not in u.lower()
        )

    if isinstance(uris, list):
        urls = [u.strip() for u in uris if is_valid(u)]

    elif isinstance(uris, dict):
        urls = [u.strip() for u in uris.values() if is_valid(u)]

    elif isinstance(uris, str):
        if is_valid(uris):
            urls = [uris.strip()]

    # prioritas m3u8
    for u in urls:
        if ".m3u8" in u.lower():
            return u

    # fallback php
    if urls:
        return urls[0]

    return None


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

    # FORMAT BARU OUTPUT2
    lines2 = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        ""
    ]

    count1 = 0
    count2 = 0

    for item in data:
        name = item.get("name", "").strip()
        uris = item.get("uris")

        # FILTER HANYA 애니플러스
        if name != TARGET_NAME:
            continue

        # OUTPUT1
        url1 = extract_m3u8_only(uris)

        if url1:
            lines1.append(f"{name},{url1}")
            count1 += 1

        # OUTPUT2
        url2 = extract_m3u8_or_php(uris)

        if url2:
            lines2.append(
                "#EXT-X-STREAM-INF:BANDWIDTH=2128000"
            )
            lines2.append(url2)
            lines2.append("")
            count2 += 1

    with open(OUTPUT1, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines1))

    with open(OUTPUT2, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines2))

    print(f"{datetime.now()} DIYP 频道数量: {count1}")
    print(f"{datetime.now()} IPTV 频道数量: {count2}")
    print(f"{datetime.now()} 已生成文件: {OUTPUT1}, {OUTPUT2}")


if __name__ == "__main__":
    run()