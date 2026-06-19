#!/usr/bin/env python3
"""
Booth / profiles 차이를 계산하는 보조 함수 모음입니다.
"""

import json
import re
from urllib.parse import urlparse


def extract_item_id_from_url(url):
    """
    Booth item URL에서 상품 ID를 추출합니다.
    예: https://sample.booth.pm/items/1234567 -> 1234567
    """
    if not url:
        return None

    match = re.search(r"/items/(\d+)", url)
    if match:
        return match.group(1)
    return None


def extract_shop_name_from_url(url):
    """
    Booth URL에서 shop 서브도메인 이름을 추출합니다.
    예: https://daikonryu.booth.pm/items/123 -> daikonryu
    """
    if not url:
        return "unknown"

    try:
        host = urlparse(url).hostname or ""
    except Exception:
        host = ""

    match = re.match(r"^([^.]+)\.booth\.pm$", host.lower())
    if match:
        return match.group(1)

    return "unknown"


def normalize_shop_name(value):
    """
    Block_Shops.txt에 적힌 값을 비교용 shop 이름으로 정규화합니다.

    허용 예시:
    - daikonryu
    - daikonryu.booth.pm
    - https://daikonryu.booth.pm/*
    """
    if value is None:
        return None

    value = value.strip().lower()
    if not value or value.startswith("#"):
        return None

    if "://" in value:
        host = urlparse(value).hostname or ""
    else:
        host = value

    host = host.replace("*", "").strip().strip("/")
    if host.startswith("www."):
        host = host[4:]
    if host.endswith(".booth.pm"):
        host = host[:-len(".booth.pm")]

    return host or None


def load_block_shops(file_path):
    """
    Block_Shops.txt에서 차단할 Booth shop 목록을 읽습니다.
    """
    shops = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                shop = normalize_shop_name(line)
                if shop:
                    shops.add(shop)
    except FileNotFoundError:
        return set()

    return shops


def filter_mapping_by_block_shops(booth_mapping, block_shops):
    """
    item_id -> url 매핑에서 차단된 shop의 항목을 제거합니다.
    """
    if not block_shops:
        return dict(booth_mapping)

    filtered = {}
    for item_id, url in booth_mapping.items():
        shop_name = extract_shop_name_from_url(url)
        if shop_name in block_shops:
            continue
        filtered[item_id] = url

    return filtered


def load_block_urls(file_path):
    """
    Block_URLs.txt / Avatar_URLs.txt에서 item ID 목록을 읽습니다.
    URL 전체를 적어도 되고, /items/<id> 형태만 추출합니다.
    """
    item_ids = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if not url or url.startswith("#"):
                    continue

                item_id = extract_item_id_from_url(url)
                if item_id:
                    item_ids.add(item_id)
    except FileNotFoundError:
        return set()

    return item_ids


def load_profiles_urls(file_path):
    """
    profiles.json에서 이미 등록된 Booth item ID를 읽습니다.

    기본 정책:
    - downloadLocation은 항상 포함
    - avatarNameUrl은 official == true 일 때만 포함
      (추가 제외 로직은 check_new_profiles.py에서 따로 병합 가능)
    """
    item_ids = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for profile in data.get("profiles", []):
            download_url = profile.get("downloadLocation", "")
            download_item_id = extract_item_id_from_url(download_url)
            if download_item_id:
                item_ids.add(download_item_id)

            if profile.get("official") is True:
                avatar_url = profile.get("avatarNameUrl", "")
                avatar_item_id = extract_item_id_from_url(avatar_url)
                if avatar_item_id:
                    item_ids.add(avatar_item_id)

    except FileNotFoundError:
        return set()
    except json.JSONDecodeError:
        return set()

    return item_ids
