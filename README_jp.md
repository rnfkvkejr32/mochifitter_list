# もちふぃったープロファイル一覧

VRChat用アバターの「もちふぃったー」対応プロファイル情報をまとめた静的Webサイトと管理ツール群。

## 内容

### Webページ

- **index.html** - メインの一覧ページ（検索・フィルター機能付き）
- **lite.html** - 軽量版一覧ページ
- **terms.html** - 利用規約ページ

### 管理ツール

- **profile_editor.py** - プロファイル編集GUI
- **booth_url_extractor.py** - Booth URLを抽出
- **diff_checker.py** - プロファイルの差分チェック
- **url_investigation.py** - URL調査ツール
- **check_new_profiles.py** - 新規プロファイル自動チェック（GitHub Actions用）

### 開発ツール

- **scripts/server.py** - ローカル開発用HTTPサーバー
- **scripts/start_server.bat** - サーバー起動用バッチファイル（Windows）

### データ

- **data/profiles.json** - プロファイル情報（アバター名、作者、配布場所など）
- **data/Block_URLs.txt** - 除外するBooth商品URL（オプション）
- **data/Avatar_URLs.txt** - 除外するアバターURL（オプション）

## ローカル開発サーバー

Webページをローカル環境で確認するための簡易HTTPサーバーを用意しています。

### 起動方法

#### Windows（バッチファイル）

1. `scripts/start_server.bat` をダブルクリック
2. 自動的にブラウザが開き、サイトが表示されます
3. 終了するには、コンソールウィンドウで `Ctrl+C` を押してください

#### コマンドライン（全OS対応）

```bash
# 基本起動（ポート8000、ブラウザ自動オープン）
python scripts/server.py

# ポート番号を指定
python scripts/server.py --port 3000

# ブラウザを開かずに起動
python scripts/server.py --no-browser

# ヘルプを表示
python scripts/server.py --help
```

### アクセスURL

サーバー起動後、以下のURLでアクセスできます：

- メインページ: `http://localhost:8000/`
- 利用規約: `http://localhost:8000/terms.html`
- 軽量版: `http://localhost:8000/lite.html`

### 必要な環境

- Python 3.6以上（標準ライブラリのみ使用、追加パッケージ不要）

## 自動チェック機能

GitHub Actionsを使用して、Boothで新しいプロファイルを自動的にチェックします。

**詳しいセットアップ方法は [SETUP_GUIDE.md](SETUP_GUIDE.md) を参照してください。**

### 設定方法（概要）

1. **Discord Webhookの設定**
   - Discordでチャンネルの設定からWebhook URLを取得
   - GitHubリポジトリの Settings > Secrets and variables > Actions
   - `DISCORD_WEBHOOK_URL` という名前でシークレットを追加

2. **実行スケジュール**
   - 2時間ごとに自動実行
   - 手動実行も可能（Actions タブから「Check New Booth Profiles」を選択）

3. **チェック対象URL**
   - `https://booth.pm/ja/browse/3Dキャラクター?q=もちふぃった`
   - `https://booth.pm/ja/browse/3Dキャラクター?q=mochifitter`
   - `https://booth.pm/ja/browse/3Dモデル（その他）?q=もちふぃった`
   - `https://booth.pm/ja/browse/3Dモデル（その他）?q=mochifitter`
   - `https://booth.pm/ja/browse/3Dツール・システム?q=もちふぃった`
   - `https://booth.pm/ja/browse/3Dツール・システム?q=mochifitter`
   - `https://booth.pm/ja/browse/VRoid?q=もちふぃった`
   - `https://booth.pm/ja/browse/VRoid?q=mochifitter`

### 動作

1. 上記の検索URLから商品URLを収集
2. `profiles.json`、`Block_URLs.txt`、`Avatar_URLs.txt` と照合
3. 未登録の商品があれば：
   - Discord Webhookで通知
   - `unregistered_avatars.txt` をArtifactとして保存（30日間）
4. 未登録の商品がなければ正常終了

## 登録作業フロー

```mermaid
flowchart TD
    Start([事前準備]) --> Setup[profile_editor.py起動]
    Setup --> Search[BOOTHでキーワード検索<br/>もちふぃった～ mochifitter等]
    Search --> Extract[booth_url_extractor.py実行<br/>→ booth_urls.txt]
    Extract --> Diff[diff_checker.py実行<br/>→ unregistered_avatars.txt]
    Diff --> Investigate[url_investigation.pyで次へ<br/>URLを開く]

    Investigate --> CheckURL{目視判定}
    CheckURL -->|1.非登録対象<br/>衣装/テクスチャ等| Block[ブロック登録<br/>Block_URLs.txt]
    CheckURL -->|2.非公式<br/>変換プロファイル| UnofficialSearch[対応アバター手動検索・調査<br/>どのアバター用か特定]
    CheckURL -->|3.公式<br/>アバターURL| Official[レコード追加<br/>自動入力: ID/登録日/更新日/配布場所Booth]

    Block --> Investigate

    UnofficialSearch --> Unofficial[レコード追加<br/>自動入力: ID/登録日/更新日/配布場所Booth]
    Unofficial --> UnofficialInput[アバターURLペースト<br/>取得ボタン押下]
    UnofficialInput --> UnofficialAuto[自動入力:<br/>アバター名/作者/作者URL/画像URL]
    UnofficialAuto --> UnofficialCheck[順方向/逆方向チェック]
    UnofficialCheck --> UnofficialDist{配布場所}

    UnofficialDist -->|Booth| UnofficialBooth[配布場所URLペースト<br/>取得ボタン押下]
    UnofficialBooth --> UnofficialBoothAuto[自動入力:<br/>プロファイル作者/作者URL]
    UnofficialBoothAuto --> UnofficialPrice{価格}

    UnofficialPrice -->|2-A.有料| UnofficialPaid[単体有料選択<br/>価格手動入力]
    UnofficialPrice -->|2-B.無料| UnofficialFree[無料ボタン押下<br/>価格 → 0]

    UnofficialPaid --> AvatarPrice
    UnofficialFree --> AvatarPrice

    UnofficialDist -->|Booth以外| UnofficialOther[配布場所URLペースト<br/>プロファイル作者/作者URL手動入力]
    UnofficialOther --> AvatarPrice

    Official --> OfficialInput[公式チェックON<br/>アバターURLペースト<br/>取得ボタン押下]
    OfficialInput --> OfficialAuto[自動入力:<br/>アバター名/作者/作者URL<br/>プロファイル作者/作者URL/画像URL]
    OfficialAuto --> OfficialCheck[順方向/逆方向チェック]
    OfficialCheck --> OfficialDist{配布方法}

    OfficialDist -->|3-A.同梱| OfficialBundle[アバター同梱ボタン押下<br/>価格 → -<br/>配布場所=アバターURL]
    OfficialBundle --> AvatarPrice

    OfficialDist -->|3-B.同じページ| OfficialSamePage{価格}
    OfficialSamePage -->|3-B-A.無料| OfficialSameFree[無料ボタン押下<br/>価格 → 0<br/>配布場所=アバターURL]
    OfficialSamePage -->|3-B-B.有料| OfficialSamePaid[単体有料選択<br/>価格手動入力<br/>配布場所=アバターURL]

    OfficialSameFree --> AvatarPrice
    OfficialSamePaid --> AvatarPrice

    OfficialDist -->|3-C.別サイト<br/>GoogleDrive等| OfficialExternal[配布場所URLに外部リンクペースト<br/>プロファイル作者/作者URL手動入力]
    OfficialExternal --> AvatarPrice

    AvatarPrice[アバター価格入力]
    AvatarPrice --> Sale{セール?}
    Sale -->|Yes| SaleInfo[セール中チェックON<br/>開始日/終了日/セール価格]
    Sale -->|No| Notes
    SaleInfo --> Notes

    Notes[備考入力<br/>任意]
    Notes --> Validate[入力状況パネルで<br/>必須項目チェック]
    Validate --> Apply[変更を適用]

    Apply --> Next{次のURL}
    Next -->|あり| Investigate
    Next -->|なし| Save[保存]

    Save --> Push[GitHubプッシュ]
    Push --> End([完了])
```

## ライセンス

MIT License
