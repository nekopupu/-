# My英単語帳 A-Z (Python ネイティブスマホアプリ版)

Python (Flet / Flutterネイティブエンジン) で書き直した、完全オフライン動作のAndroidアプリです。

## 特徴
- **100%ネイティブ動作**: WebViewやHTMLではないため、上にスクロールしてもリフレッシュ誤爆が起きず、起動も一瞬です。
- **完全オフライン・ログイン不要**: 単語データはスマホ端末内の専用ストレージへ自動保存されます。
- **モンドリアン (De Stijl) デザイン**: お手元のデザインとアイコン画像 (`icon-512.png`) をそのまま組み込んでいます。
- **他AIのJSON貼付対応**: 上部の青い「JSON貼付」ボタンから、他AIが出力したJSONテキストをそのままマージできます。

---

## APKを無料で自動生成する手順（PCへのAndroid環境構築不要）

1. **GitHub** (https://github.com) で新しいリポジトリを作成します（PrivateでもOK）。
2. このフォルダの中身（`src`、`pyproject.toml`、`.github` フォルダ）をすべてアップロードします。
3. GitHubリポジトリ上部の **「Actions」** タブを開くと、自動で **Build Android APK** が動き始めます（約5〜10分）。
4. 完了したらワークフローをクリックし、下部の **Artifacts → `my-vocab-az-apk`** をクリックしてダウンロードします。
5. 解凍して出てきた **`app-release.apk`** をAndroidスマホに送ってインストールすれば完了です。

## PCで先に動作確認したい場合
```bash
pip install flet
flet run src/main.py
```
