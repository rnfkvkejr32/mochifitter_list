#!/usr/bin/env python3
"""
profiles.json 内で avatarshopname / profileshopname が空のものを一覧表示するスクリプト。
"""

import json
import os


def list_missing(json_path: str) -> int:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    missing = []

    for p in profiles:
        avatar_missing = not p.get("avatarshopname")
        download_url = p.get("downloadLocation", "") or ""
        is_booth = "booth.pm" in download_url
        # Boothでない配布URLの場合は profileshopname の欠落は無視
        profile_missing = (not p.get("profileshopname")) and is_booth
        if avatar_missing or profile_missing:
            missing.append({
                "avatarNameUrl": p.get("avatarNameUrl"),
                "downloadLocation": p.get("downloadLocation"),
            })

    if not missing:
        print("すべてのショップ名が埋まっています。")
        return 0

    print(f"不足しているプロファイル数: {len(missing)}")
    for m in missing:
        print(f"avatarUrl={m['avatarNameUrl']}  download={m['downloadLocation']}")
    return len(missing)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    json_path = os.path.join(repo_root, "data", "profiles.json")
    if not os.path.exists(json_path):
        print(f"profiles.json が見つかりません: {json_path}")
        return 1
    list_missing(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

