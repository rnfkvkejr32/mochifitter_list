@echo off
chcp 65001 >nul
REM ローカル開発用HTTPサーバー起動スクリプト（Windows用）

echo.
echo ======================================================
echo   もちふぃった～プロファイル一覧
echo   ローカル開発用サーバー起動
echo ======================================================
echo.

REM Pythonがインストールされているか確認
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [エラー] Pythonが見つかりません。
    echo.
    echo Pythonをインストールしてから再度実行してください。
    echo ダウンロード: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Pythonのバージョンを表示
echo Pythonバージョン:
python --version
echo.

REM スクリプトのディレクトリを取得
set SCRIPT_DIR=%~dp0
REM プロジェクトルート（scriptsの親ディレクトリ）に移動
cd /d "%SCRIPT_DIR%.."

REM server.pyが存在するか確認
if not exist "scripts\server.py" (
    echo [エラー] scripts\server.py が見つかりません。
    echo.
    echo プロジェクトの構造が正しいか確認してください。
    echo.
    pause
    exit /b 1
)

REM サーバーを起動
echo サーバーを起動しています...
echo.
python scripts\server.py

REM サーバーが停止した場合
echo.
echo サーバーが停止しました。
pause
