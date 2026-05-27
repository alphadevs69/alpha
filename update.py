from datetime import datetime
import requests

JSON_URL = "http://141.164.53.195/live/korea-live.json"

OUTPUT2 = "Aniplus.m3u8"

TARGET_NAME = "애니플러스"


def extract_url(uris):

    def is_valid(u):
        return (
            isinstance(u, str)
            and ".m3u8" in u.lower()
            and "wavve" not in u.lower()
            and "file-1253962976.cos" not in u.lower()
        )

    if isinstance(uris, list):
        for u in uris:
            if is_valid(u):
                return u.strip()

    elif isinstance(uris, dict):
        for u in uris.values():
            if is_valid(u):
                return u.strip()

    elif isinstance(uris, str):
        if is_valid(uris):
            return uris.strip()

    return None


def run():

    try:
        r = requests.get(
            JSON_URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        r.raise_for_status()

        data = r.json()

    except Exception as e:
        print(f"JSON ERROR: {e}")
        return

    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        ""
    ]

    for item in data:

        name = item.get("name", "").strip()

        if name != TARGET_NAME:
            continue

        url = extract_url(
            item.get("uris")
        )

        if not url:
            continue

        lines.append(
            '#EXT-X-STREAM-INF:BANDWIDTH=2192000,RESOLUTION=1280x720'
        )

        lines.append(url)

        break

    with open(
        OUTPUT2,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as f:

        f.write("\n".join(lines))

    print(
        f"{datetime.now()} GENERATED: {OUTPUT2}"
    )


if __name__ == "__main__":
    run()