import json
import os

# プロジェクトのルートディレクトリ
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json_path = os.path.join(project_root, 'data', 'profiles.json')

# JSONファイルを読み込み
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 処理カウンター
free_count = 0
bundled_count = 0

# 各プロファイルを処理
for profile in data['profiles']:
    # 1. pricing が "無料" のもの → price を "0" に設定
    if profile.get('pricing') == '無料':
        old_price = profile.get('price', '')
        if old_price != '0':
            profile['price'] = '0'
            free_count += 1
            print(f"[無料] {profile['id']}: {profile['avatarName']} - price: {old_price} → 0")

    # 2. pricing が "アバター同梱" で price が 1以上の数値
    elif profile.get('pricing') == 'アバター同梱':
        price_str = str(profile.get('price', '')).strip()
        # "-" や空文字列でない、数値に変換可能なもの
        if price_str and price_str != '-':
            try:
                price_num = int(price_str)
                if price_num >= 1:
                    # avatarPriceが空または未設定の場合のみ移動
                    avatar_price = str(profile.get('avatarPrice', '')).strip()
                    if not avatar_price:
                        profile['avatarPrice'] = price_str
                        profile['price'] = '-'
                        bundled_count += 1
                        print(f"[アバター同梱] {profile['id']}: {profile['avatarName']} - price: {price_str} → avatarPrice, price → -")
            except ValueError:
                # 数値に変換できない場合はスキップ
                pass

# 結果を保存
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n処理完了:")
print(f"- 無料プロファイルのprice修正: {free_count}件")
print(f"- アバター同梱のprice→avatarPrice移動: {bundled_count}件")
