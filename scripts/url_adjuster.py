import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
import re
import threading


class URLAdjusterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BOOTH URL Adjuster")
        self.root.geometry("1000x600")

        # メインフレーム
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 左側: 入力エリア
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        ttk.Label(left_frame, text="入力URL (改行区切り):").grid(row=0, column=0, sticky=tk.W)
        self.input_text = scrolledtext.ScrolledText(left_frame, width=45, height=30)
        self.input_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 右側: 出力エリア
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        ttk.Label(right_frame, text="出力URL (改行区切り):").grid(row=0, column=0, sticky=tk.W)
        self.output_text = scrolledtext.ScrolledText(right_frame, width=45, height=30)
        self.output_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.convert_button = ttk.Button(button_frame, text="変換", command=self.start_conversion)
        self.convert_button.grid(row=0, column=0, padx=5)

        ttk.Button(button_frame, text="クリア", command=self.clear_all).grid(row=0, column=1, padx=5)

        # ステータスバー
        self.status_label = ttk.Label(main_frame, text="待機中", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

        # グリッド設定
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

    def clear_all(self):
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.status_label.config(text="クリアしました")

    def start_conversion(self):
        # 別スレッドで実行
        thread = threading.Thread(target=self.convert_urls)
        thread.daemon = True
        thread.start()

    def convert_urls(self):
        self.convert_button.config(state=tk.DISABLED)
        self.output_text.delete(1.0, tk.END)

        input_urls = self.input_text.get(1.0, tk.END).strip().split('\n')
        input_urls = [url.strip() for url in input_urls if url.strip()]

        if not input_urls:
            self.status_label.config(text="URLが入力されていません")
            self.convert_button.config(state=tk.NORMAL)
            return

        total = len(input_urls)
        results = []

        for idx, url in enumerate(input_urls, 1):
            self.status_label.config(text=f"処理中: {idx}/{total}")
            converted_url = self.adjust_url(url)
            results.append(converted_url)
            self.output_text.insert(tk.END, converted_url + '\n')
            self.output_text.see(tk.END)
            self.root.update()

        self.status_label.config(text=f"完了: {total}件のURL処理完了")
        self.convert_button.config(state=tk.NORMAL)

    def adjust_url(self, url):
        # 既にショップ名が含まれているかチェック
        # https://shop.booth.pm/items/123 形式ならそのまま
        if re.match(r'https://[^/]+\.booth\.pm/items/\d+', url):
            return url

        # https://booth.pm/ja/items/123 形式の場合のみ処理
        match = re.match(r'https://booth\.pm/ja/items/(\d+)', url)
        if not match:
            return url

        item_id = match.group(1)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # ショップリンクを取得
            shop_link = soup.find('a', href=re.compile(r'https://[^/]+\.booth\.pm/?$'))

            if shop_link and shop_link.get('href'):
                shop_url = shop_link.get('href').rstrip('/')
                # ショップ名を抽出
                shop_match = re.match(r'https://([^/]+)\.booth\.pm', shop_url)
                if shop_match:
                    shop_name = shop_match.group(1)
                    return f"https://{shop_name}.booth.pm/items/{item_id}"

            return url

        except Exception as e:
            print(f"Error processing {url}: {e}")
            return url


def main():
    root = tk.Tk()
    app = URLAdjusterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
