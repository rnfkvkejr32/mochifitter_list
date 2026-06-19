#!/usr/bin/env python3
"""
Booth에서 새로운 Mochifitter 대응 프로필을 자동으로 확인하는 스크립트입니다.
GitHub Actions에서 실행되는 것을 기준으로 작성되었습니다.
"""

import sys
import os
import json
import requests
from datetime import datetime

# 기존 모듈 가져오기
sys.path.append(os.path.dirname(__file__))
from booth_url_extractor import extract_booth_urls
from diff_checker import (
    extract_item_id_from_url,
    extract_shop_name_from_url,
    filter_mapping_by_block_shops,
    load_block_shops,
    load_profiles_urls,
    load_block_urls,
)


def collect_urls_from_searches(search_urls):
    """
    여러 검색 URL에서 상품 URL을 수집합니다.

    Args:
        search_urls: 검색 URL 목록

    Returns:
        dict: item_id -> url 매핑
    """
    all_urls = {}

    for search_url in search_urls:
        print(f"\n검색 URL: {search_url}")
        print("-" * 80)

        urls = extract_booth_urls(search_url)

        for url in urls:
            item_id = extract_item_id_from_url(url)
            if item_id:
                all_urls[item_id] = url

        print(f"이 검색에서 {len(urls)}건의 상품을 발견")

    return all_urls


def load_all_avatar_name_url_ids(profiles_file):
    """
    profiles.json의 avatarNameUrl에서 item ID를 모두 가져옵니다.
    official 값과 관계없이, 이미 알고 있는 아바타 본체 상품을 신규 후보에서 제외하기 위한 용도입니다.
    """
    item_ids = set()

    try:
        with open(profiles_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for profile in data.get("profiles", []):
            avatar_url = profile.get("avatarNameUrl", "")
            item_id = extract_item_id_from_url(avatar_url)
            if item_id:
                item_ids.add(item_id)

    except FileNotFoundError:
        print(f"경고: {profiles_file} 파일을 찾을 수 없습니다")
    except json.JSONDecodeError:
        print(f"경고: {profiles_file} JSON 파싱에 실패했습니다")

    return item_ids


def find_unregistered_items(booth_mapping, profiles_file, block_file, avatar_file, block_shop_file):
    """
    아직 등록되지 않은 아이템을 찾습니다.

    Args:
        booth_mapping: item_id -> url 매핑
        profiles_file: profiles.json 경로
        block_file: Block_URLs.txt 경로
        avatar_file: Avatar_URLs.txt 경로
        block_shop_file: Block_Shops.txt 경로

    Returns:
        list: 미등록 아이템의 (shop_name, url) 튜플 목록
    """
    # profiles.json에서 등록된 ID 가져오기
    profile_ids = load_profiles_urls(profiles_file)
    avatar_name_ids = load_all_avatar_name_url_ids(profiles_file)
    profile_ids = profile_ids | avatar_name_ids

    # Block 파일들에서 제외 ID / shop 가져오기
    block_ids = load_block_urls(block_file)
    avatar_ids = load_block_urls(avatar_file)
    block_shops = load_block_shops(block_shop_file)

    # 샵 차단 적용
    filtered_mapping = filter_mapping_by_block_shops(booth_mapping, block_shops)
    booth_ids = set(filtered_mapping.keys())

    print(f"\nBooth 검색 상품 수: {len(booth_mapping)}")
    print(f"Block_Shops.txt 차단 샵 수: {len(block_shops)}")
    print(f"샵 차단 적용 후 상품 수: {len(booth_ids)}")
    print(f"profiles.json에 등록된 상품 수: {len(profile_ids)}")
    print(f"Block_URLs.txt 차단 수: {len(block_ids)}")
    print(f"Avatar_URLs.txt 차단 수: {len(avatar_ids)}")

    # 차이 계산
    diff_ids = booth_ids - profile_ids - block_ids - avatar_ids

    if not diff_ids:
        return []

    # URL과 샵 이름 목록 생성
    url_list = []
    for item_id in diff_ids:
        url = filtered_mapping[item_id]
        shop_name = extract_shop_name_from_url(url)
        url_list.append((shop_name, url))

    # 샵 이름 기준 정렬
    url_list.sort(key=lambda x: x[0])

    return url_list


def send_discord_notification(webhook_url, unregistered_items, site_url, mention):
    """
    Discord Webhook으로 알림을 전송합니다.

    Args:
        webhook_url: Discord Webhook URL
        unregistered_items: 미등록 아이템의 (shop_name, url) 튜플 목록
        site_url: Mochifitter 사이트 주소
        mention: Discord 멘션 문자열

    Returns:
        bool: 전송 성공 여부
    """
    if not webhook_url:
        print("경고: Discord Webhook URL이 설정되어 있지 않습니다")
        return False

    count = len(unregistered_items)

    # 건수에 따라 표시 개수 조정
    # Discord embed description은 최대 4096자입니다.
    if count >= 50:
        max_display = 10
    elif count >= 30:
        max_display = 15
    else:
        max_display = 20

    items_to_show = unregistered_items[:max_display]
    items_text = "\n".join([f"- {url}" for _, url in items_to_show])

    description_parts = [
        f"Booth에서 새로운 Mochifitter 대응 프로필이 **{count}건** 발견되었습니다.",
        f"사이트 바로가기: {site_url}",
    ]

    if count > max_display:
        description_parts.append(f"\n**처음 {max_display}건 미리보기:**")
        description_parts.append(f"\n{items_text}")
        description_parts.append(f"\n\n**...그 외 {count - max_display}건**")
    else:
        description_parts.append(f"\n{items_text}")

    embed = {
        "title": f"🔔 새로운 프로필 {count}건 발견",
        "description": "\n".join(description_parts),
        "color": 3447003,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "MochiFitter 프로필 체커"
        }
    }

    payload = {
        "content": mention,
        "embeds": [embed]
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        print(f"\nDiscord 알림을 전송했습니다 ({count}건)")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n오류: Discord 알림 전송에 실패했습니다: {e}")
        return False


def main():
    """메인 처리"""
    print("=" * 80)
    print("신규 프로필 체커")
    print("=" * 80)

    # 검색 URL 목록
    # 일본어 검색어와 카테고리명은 URL 인코딩해서 파일 안에 일본어가 남지 않도록 했습니다.
    search_urls = [
        "https://booth.pm/ja/browse/3D%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC?q=%E3%82%82%E3%81%A1%E3%81%B5%E3%81%83%E3%81%A3%E3%81%9F",
        "https://booth.pm/ja/browse/3D%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC?q=mochifitter",
        "https://booth.pm/ja/browse/3D%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC?q=Mochi%20Fitter",
        "https://booth.pm/ja/browse/3D%E3%83%A2%E3%83%87%E3%83%AB%EF%BC%88%E3%81%9D%E3%81%AE%E4%BB%96%EF%BC%89?q=%E3%82%82%E3%81%A1%E3%81%B5%E3%81%83%E3%81%A3%E3%81%9F",
        "https://booth.pm/ja/browse/3D%E3%83%A2%E3%83%87%E3%83%AB%EF%BC%88%E3%81%9D%E3%81%AE%E4%BB%96%EF%BC%89?q=mochifitter",
        "https://booth.pm/ja/browse/3D%E3%83%A2%E3%83%87%E3%83%AB%EF%BC%88%E3%81%9D%E3%81%AE%E4%BB%96%EF%BC%89?q=Mochi%20Fitter",
        "https://booth.pm/ja/browse/3D%E3%83%84%E3%83%BC%E3%83%AB%E3%83%BB%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0?q=%E3%82%82%E3%81%A1%E3%81%B5%E3%81%83%E3%81%A3%E3%81%9F",
        "https://booth.pm/ja/browse/3D%E3%83%84%E3%83%BC%E3%83%AB%E3%83%BB%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0?q=mochifitter",
        "https://booth.pm/ja/browse/3D%E3%83%84%E3%83%BC%E3%83%AB%E3%83%BB%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0?q=Mochi%20Fitter",
        "https://booth.pm/ja/browse/VRoid?q=%E3%82%82%E3%81%A1%E3%81%B5%E3%81%83%E3%81%A3%E3%81%9F",
        "https://booth.pm/ja/browse/VRoid?q=mochifitter",
        "https://booth.pm/ja/browse/VRoid?q=Mochi%20Fitter",
    ]

    # 파일 경로
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profiles_file = os.path.join(base_dir, "data", "profiles.json")
    block_file = os.path.join(base_dir, "data", "Block_URLs.txt")
    avatar_file = os.path.join(base_dir, "data", "Avatar_URLs.txt")
    block_shop_file = os.path.join(base_dir, "data", "Block_Shops.txt")
    output_file = os.path.join(base_dir, "unregistered_avatars.txt")

    # 환경 변수
    discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")
    discord_mention = os.environ.get("DISCORD_MENTION", "<@327084452503224320>")
    site_url = os.environ.get("MOCHIFITTER_SITE_URL", "http://mochi.vr-chat.kr")

    # 상품 URL 수집
    print("\n상품 URL을 수집하는 중...")
    booth_mapping = collect_urls_from_searches(search_urls)
    print(f"\n총 {len(booth_mapping)}건의 상품을 수집했습니다")

    # 미등록 아이템 감지
    print("\n차이를 확인하는 중...")
    print("=" * 80)
    unregistered_items = find_unregistered_items(
        booth_mapping, profiles_file, block_file, avatar_file, block_shop_file
    )

    if unregistered_items:
        print(f"\n미등록 아바타 수: {len(unregistered_items)}")
        print("\n미등록 아바타 URL 목록:")
        print("-" * 80)

        for shop_name, url in unregistered_items:
            print(url)

        # 파일에 저장
        with open(output_file, "w", encoding="utf-8") as f:
            for shop_name, url in unregistered_items:
                f.write(url + "\n")

        print("-" * 80)
        print(f"\n결과를 {output_file}에 저장했습니다")

        # Discord 알림
        if discord_webhook:
            send_discord_notification(
                discord_webhook,
                unregistered_items,
                site_url,
                discord_mention
            )
        else:
            print("\n주의: DISCORD_WEBHOOK_URL 환경 변수가 설정되어 있지 않아 알림을 건너뜁니다")

        # 신규 아이템이 있으면 종료 코드 1을 반환합니다.
        # GitHub Actions에서 신규 아이템 발견 여부를 감지할 수 있습니다.
        sys.exit(1)

    print("\n모든 아바타가 이미 등록되어 있습니다")
    sys.exit(0)


if __name__ == "__main__":
    main()
