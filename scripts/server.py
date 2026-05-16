#!/usr/bin/env python3
"""
ローカル開発用HTTPサーバー

静的ファイルを配信する簡易HTTPサーバーを起動します。
デフォルトでポート8000で起動し、ブラウザを自動で開きます。
"""

import argparse
import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path
from threading import Timer


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """カスタムHTTPリクエストハンドラー"""
    
    def end_headers(self):
        """CORSヘッダーを追加"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        sys.stdout.write("%s - [%s] %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         format % args))


def open_browser(url, delay=1.5):
    """指定されたURLをブラウザで開く（遅延付き）"""
    def _open():
        webbrowser.open(url)
    Timer(delay, _open).start()


def find_project_root():
    """プロジェクトルートを見つける（index.htmlがあるディレクトリ）"""
    current = Path(__file__).parent
    
    # scriptsディレクトリから親ディレクトリに移動
    if current.name == 'scripts':
        parent = current.parent
        if (parent / 'index.html').exists():
            return parent
    
    # カレントディレクトリにindex.htmlがあるか確認
    if (current / 'index.html').exists():
        return current
    
    # 親ディレクトリにindex.htmlがあるか確認
    if (current.parent / 'index.html').exists():
        return current.parent
    
    # 見つからない場合はカレントディレクトリを返す
    return Path.cwd()


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='ローカル開発用HTTPサーバーを起動します',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python scripts/server.py                    # デフォルト設定で起動
  python scripts/server.py --port 3000        # ポート3000で起動
  python scripts/server.py --no-browser       # ブラウザを開かずに起動
  python scripts/server.py -p 8080 --no-browser
        """
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=8000,
        help='サーバーのポート番号 (デフォルト: 8000)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='ブラウザを自動で開かない'
    )
    
    args = parser.parse_args()
    
    # ポート番号の妥当性チェック
    if args.port < 1 or args.port > 65535:
        print(f"エラー: ポート番号は1-65535の範囲で指定してください")
        sys.exit(1)
    
    # プロジェクトルートに移動
    project_root = find_project_root()
    os.chdir(project_root)
    
    # ドキュメントルートを表示
    print(f"\n{'='*60}")
    print(f"  ローカル開発用HTTPサーバー")
    print(f"{'='*60}")
    print(f"ドキュメントルート: {project_root}")
    print(f"ポート番号: {args.port}")
    print(f"{'='*60}\n")
    
    # サーバーのURLを構築
    server_url = f"http://localhost:{args.port}"
    
    # サーバーを起動
    try:
        with socketserver.TCPServer(("", args.port), CustomHTTPRequestHandler) as httpd:
            print(f"サーバーを起動しました: {server_url}")
            print(f"\nアクセスURL:")
            print(f"  - {server_url}/")
            print(f"  - {server_url}/index.html")
            print(f"  - {server_url}/terms.html")
            print(f"  - {server_url}/lite.html")
            print(f"\n終了するには Ctrl+C を押してください\n")
            
            # ブラウザを開く
            if not args.no_browser:
                print("ブラウザを開いています...")
                open_browser(server_url)
            
            # サーバーを実行
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48 or e.errno == 10048:  # Address already in use
            print(f"\nエラー: ポート {args.port} は既に使用されています")
            print(f"別のポート番号を指定してください:")
            print(f"  python scripts/server.py --port {args.port + 1}")
        else:
            print(f"\nエラー: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nサーバーを停止しました")
        print("お疲れ様でした！\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
