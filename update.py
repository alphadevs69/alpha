from datetime import datetime
import requests

JSON_URL = "http://141.164.53.195/live/korea-live.json"

OUTPUT1 = "Aniplus2.m3u8"   # DIYP
OUTPUT2 = "Aniplus.m3u8"    # IPTV

# Jangan bergantung pada name persis, karena sumber bisa ganti nama
TARGET_KEYWORDS = [
    "애니플러스",
    "aniplus",
    "ani plus",
]

# Petunjuk tambahan dari URL TVING/Aniplus
TARGET_URL_HINTS = [
    "aniplus",
    "live5000.smil",
    "channel_code=C00901",
    "program_code=P001751877",
]

BLOCKLIST = [
    "wavve",
    "file-1253962976.cos",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}


def flatten_urls(value):
    """Ambil semua URL dari uris walaupun bentuknya list/dict/string/nested."""
    urls = []

    if isinstance(value, str):
        urls.append(value.strip())
    elif isinstance(value, list):
        for item in value:
            urls.extend(flatten_urls(item))
    elif isinstance(value, dict):
        for item in value.values():
            urls.extend(flatten_urls(item))

    return [u for u in urls if u]


def is_blocked(url):
    low = url.lower()
    return any(b in low for b in BLOCKLIST)


def is_m3u8(url):
    return isinstance(url, str) and ".m3u8" in url.lower() and not is_blocked(url)


def is_php(url):
    low = url.lower()
    return isinstance(url, str) and low.endswith(".php") and not is_blocked(url)


def item_is_target(item, urls):
    """Cocokkan dari name/title/channel_name atau dari isi URL."""
    text_parts = []

    for key in ["name", "title", "channel", "channel_name", "group", "id", "code"]:
        val = item.get(key)
        if val is not None:
            text_parts.append(str(val))

    text = " ".join(text_parts).lower()
    joined_urls = " ".join(urls).lower()

    if any(k.lower() in text for k in TARGET_KEYWORDS):
        return True

    if any(h.lower() in joined_urls for h in TARGET_URL_HINTS):
        return True

    return False


def pick_url(urls, allow_php=False):
    """Prioritas URL m3u8 TVING/Aniplus, lalu m3u8 lain, lalu php jika diizinkan."""
    valid_m3u8 = [u for u in urls if is_m3u8(u)]

    # Prioritas URL yang mengandung hint target
    for u in valid_m3u8:
        low = u.lower()
        if any(h.lower() in low for h in TARGET_URL_HINTS):
            return u

    if valid_m3u8:
        return valid_m3u8[0]

    if allow_php:
        valid_php = [u for u in urls if is_php(u)]
        if valid_php:
            return valid_php[0]

    return None


def run():
    try:
        r = requests.get(JSON_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"{datetime.now()} 获取 JSON 失败: {e}")
        return

    if not isinstance(data, list):
        print(f"{datetime.now()} JSON bukan list, tipe: {type(data).__name__}")
        return

    lines1 = ["#EXTM3U"]
    lines2 = ["#EXTM3U", "#EXT-X-VERSION:3", ""]

    count1 = 0
    count2 = 0
    found_names = []

    for item in data:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name") or item.get("title") or "Aniplus").strip()
        urls = flatten_urls(item.get("uris"))

        if not urls:
            continue

        if not item_is_target(item, urls):
            continue

        found_names.append(name)

        url1 = pick_url(urls, allow_php=False)
        if url1:
            lines1.append(f"{name},{url1}")
            count1 += 1

        url2 = pick_url(urls, allow_php=True)
        if url2:
            lines2.append("#EXT-X-STREAM-INF:BANDWIDTH=2128000")
            lines2.append(url2)
            lines2.append("")
            count2 += 1

    with open(OUTPUT1, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines1) + "\n")

    with open(OUTPUT2, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines2) + "\n")

    print(f"{datetime.now()} Target cocok: {', '.join(found_names) if found_names else 'tidak ada'}")
    print(f"{datetime.now()} DIYP 频道数量: {count1}")
    print(f"{datetime.now()} IPTV 频道数量: {count2}")
    print(f"{datetime.now()} 已生成文件: {OUTPUT1}, {OUTPUT2}")


if __name__ == "__main__":
    run()
