#!/usr/bin/env python3
"""
profiles.json で必須項目が未入力の ID を列挙するスクリプト。
必須項目の定義は profile_editor.py のバリデーションに合わせる。
- downloadLocation / profileshopname は downloadLocation が Booth URL のときのみ必須。
- それ以外の必須項目は常にチェック。
出力は未入力があるプロファイルの ID のみ（1行1ID）。
"""

import json
import os


def has_value(v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    return True


def list_missing_ids(json_path: str) -> int:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    missing_ids = []

    required_fields = [
        "id",
        "avatarName",
        "avatarNameUrl",
        "profileVersion",
        "avatarAuthor",
        "avatarAuthorUrl",
        "avatarshopname",
        "profileAuthor",
        "profileAuthorUrl",
        "profileshopname",   # conditional (Booth only)
        "downloadMethod",
        "downloadLocation",  # conditional (Booth only)
        "imageUrl",
        "pricing",
        "price",
        "avatarPrice",
    ]

    for p in profiles:
        download_url = (p.get("downloadLocation") or "")
        is_booth_download = "booth.pm" in download_url

        missing = False
        for field in required_fields:
            if field in ("downloadLocation", "profileshopname") and not is_booth_download:
                continue
            if not has_value(p.get(field)):
                missing = True
                break

        if missing:
            missing_ids.append(p.get("id"))

    if not missing_ids:
        print("未入力の必須項目はありません。")
        return 0

    for mid in missing_ids:
        print(mid)
    return len(missing_ids)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    json_path = os.path.join(repo_root, "data", "profiles.json")
    if not os.path.exists(json_path):
        print(f"profiles.json が見つかりません: {json_path}")
        return 1
    list_missing_ids(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

