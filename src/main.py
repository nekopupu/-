import json
import os
import re
import time
import uuid
import flet as ft

# ==========================================
# De Stijl (ピート・モンドリアン) カラーパレット
# ==========================================
CANVAS = "#FAF8F2"
INK = "#111111"
MRED = "#D4261E"
MBLUE = "#18479E"
MYELLOW = "#F2C71E"
MGRAY = "#E9E7E0"
WHITE = "#FFFFFF"
MUTED = "#555555"

SAMPLE_JSON = """{
  "word": "excess",
  "phonetic": "/ˈek.ses/",
  "partOfSpeech": "adj. / n.",
  "inflections": "複数形: excesses",
  "meaning_ja": "余分な、過剰な、超過",
  "meaning_zh": "额外的、过多的、多余的",
  "examples": [
    {
      "en": "Passengers have to pay a fee for excess baggage.",
      "ja": "乗客は超過手荷物料金を支払わなければならない。",
      "zh": "乘客必须为超重行李支付费用。",
      "note": "形容詞は名詞の前（限定用法）でのみ使用。"
    }
  ],
  "similar_form": [
    {
      "word": "access",
      "pos": "n. / v.",
      "meaning_ja": "接近、入口、利用権",
      "meaning_zh": "通道、入口、获取",
      "note": "スペルと発音に注意"
    }
  ],
  "similar_meaning": [
    {
      "word": "extra",
      "pos": "adj.",
      "meaning_ja": "追加の、余分の",
      "meaning_zh": "额外的、附加的",
      "note": "中立的で口語的"
    }
  ]
}"""

DEFAULT_WORDS = [
    {
        "id": "init-excess",
        "word": "excess",
        "phonetic": "adj. /ˈek.ses/  n. /ɪkˈses/",
        "partOfSpeech": "adj. / n.",
        "inflections": "複数形: excesses（過度な行為） / 比較級・最上級なし",
        "meaning_ja": "余分な、過剰な、超過",
        "meaning_zh": "额外的、过多的、多余的",
        "examples": [
            {
                "en": "Passengers have to pay a fee for excess baggage.",
                "ja": "乗客は超過（追加）手荷物に対して料金を支払わなければならない。",
                "zh": "乘客必须为超重（额外）的行李支付费用。",
                "note": "形容詞は名詞の前（限定用法）でのみ使用。be excess とは言えない。",
            },
            {
                "en": "Regular exercise helps your body burn excess fat.",
                "ja": "定期的な運動は体の余分な脂肪を燃やすのに役立つ。",
                "zh": "规律运动有助于身体燃烧多余的脂肪。",
                "note": "正常な必要量を超えた「余分・過剰」のニュアンス。",
            },
            {
                "en": "An excess of salt in your diet can lead to high blood pressure.",
                "ja": "食事での塩分の過剰摂取は高血圧につながる可能性がある。",
                "zh": "饮食中摄入过多的盐会导致高血压。",
                "note": "an excess of ~（過度の〜）、in excess of ~（〜を超えて）。",
            },
        ],
        "similar_form": [
            {
                "word": "access",
                "pos": "n. / v.",
                "meaning_ja": "接近、入口、利用権",
                "meaning_zh": "通道、入口、获取",
                "note": "/ˈæk.ses/ 発音とスペルの先頭に注意",
            },
            {
                "word": "assess",
                "pos": "v.",
                "meaning_ja": "評価する、査定する",
                "meaning_zh": "评估、评定",
                "note": "/əˈses/ リスクや価値を評価する",
            },
            {
                "word": "exceed",
                "pos": "v.",
                "meaning_ja": "超える、上回る",
                "meaning_zh": "超过、超越",
                "note": "excess の同源動詞",
            },
        ],
        "similar_meaning": [
            {
                "word": "extra",
                "pos": "adj.",
                "meaning_ja": "追加の、余分の",
                "meaning_zh": "额外的、附加的",
                "note": "最も口語的で中立的（マイナス印象なし）",
            },
            {
                "word": "excessive",
                "pos": "adj.",
                "meaning_ja": "過度な、やりすぎの",
                "meaning_zh": "过多的、过分的",
                "note": "明確に否定的なニュアンス。補語にも使える",
            },
            {
                "word": "redundant",
                "pos": "adj.",
                "meaning_ja": "余剰の、くどい",
                "meaning_zh": "多余的、冗余的",
                "note": "重複や不要になったため余っている",
            },
        ],
    }
]


# ==========================================
# ローカル永続ストレージ (完全オフライン)
# ==========================================
def get_data_file_path() -> str:
    data_dir = os.environ.get("FLET_APP_STORAGE_DATA")
    if not data_dir:
        data_dir = os.path.join(os.path.expanduser("~"), ".my_vocab_az")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "vocab_data.json")


def load_words() -> list:
    path = get_data_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return sort_words(data)
        except Exception:
            pass
    words = json.loads(json.dumps(DEFAULT_WORDS))
    save_words(words)
    return words


def save_words(words: list) -> None:
    sort_words(words)
    path = get_data_file_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


def get_initial_letter(word_str: str) -> str:
    m = re.search(r"[A-Za-z]", str(word_str or ""))
    return m.group(0).upper() if m else "#"


def sort_words(words: list) -> list:
    words.sort(key=lambda w: str(w.get("word", "")).strip().lower())
    return words


# ==========================================
# 他AIのJSON自動抽出・柔軟マッピング
# ==========================================
def extract_json_from_text(text: str):
    s = str(text or "").strip()
    if not s:
        raise ValueError("テキストが空です")

    code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if code_match:
        s = code_match.group(1).strip()

    try:
        return json.loads(s)
    except json.JSONDecodeError:
        first_arr = s.find("[")
        first_obj = s.find("{")
        start, end = -1, -1
        if first_arr != -1 and (first_obj == -1 or first_arr < first_obj):
            start = first_arr
            end = s.rfind("]")
        elif first_obj != -1:
            start = first_obj
            end = s.rfind("}")
        if start != -1 and end > start:
            return json.loads(s[start : end + 1])
        raise


def normalize_entry(raw: dict):
    if not isinstance(raw, dict):
        return None
    word = str(
        raw.get("word")
        or raw.get("term")
        or raw.get("english")
        or raw.get("en")
        or raw.get("headword")
        or ""
    ).strip()
    if not word:
        return None

    def norm_examples(arr):
        if not isinstance(arr, list):
            return []
        res = []
        for e in arr:
            if isinstance(e, str):
                res.append({"en": e.strip(), "ja": "", "zh": "", "note": ""})
            elif isinstance(e, dict):
                en = str(e.get("en") or e.get("english") or e.get("sentence") or "").strip()
                ja = str(e.get("ja") or e.get("japanese") or e.get("jp") or e.get("translation_ja") or "").strip()
                zh = str(e.get("zh") or e.get("chinese") or e.get("cn") or e.get("translation_zh") or "").strip()
                note = str(e.get("note") or e.get("notes") or e.get("tip") or "").strip()
                if en or ja or zh:
                    res.append({"en": en, "ja": ja, "zh": zh, "note": note})
        return res

    def norm_rel(arr):
        if not isinstance(arr, list):
            return []
        res = []
        for r in arr:
            if isinstance(r, str):
                res.append({"word": r.strip(), "pos": "", "meaning_ja": "", "meaning_zh": "", "note": ""})
            elif isinstance(r, dict):
                rw = str(r.get("word") or r.get("term") or r.get("en") or "").strip()
                if not rw:
                    continue
                res.append(
                    {
                        "word": rw,
                        "pos": str(r.get("pos") or r.get("partOfSpeech") or "").strip(),
                        "meaning_ja": str(r.get("meaning_ja") or r.get("japanese") or r.get("ja") or r.get("meaning") or "").strip(),
                        "meaning_zh": str(r.get("meaning_zh") or r.get("chinese") or r.get("zh") or "").strip(),
                        "note": str(r.get("note") or r.get("diff") or r.get("nuance") or "").strip(),
                    }
                )
        return res

    return {
        "id": str(raw.get("id") or f"w-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"),
        "word": word,
        "phonetic": str(raw.get("phonetic") or raw.get("ipa") or raw.get("pronunciation") or "").strip(),
        "partOfSpeech": str(raw.get("partOfSpeech") or raw.get("pos") or raw.get("part_of_speech") or "").strip(),
        "inflections": str(raw.get("inflections") or raw.get("forms") or raw.get("conjugation") or "").strip(),
        "meaning_ja": str(raw.get("meaning_ja") or raw.get("japanese") or raw.get("ja") or raw.get("meaning") or "").strip(),
        "meaning_zh": str(raw.get("meaning_zh") or raw.get("chinese") or raw.get("zh") or "").strip(),
        "examples": norm_examples(raw.get("examples") or raw.get("sentences")),
        "similar_form": norm_rel(raw.get("similar_form") or raw.get("similarForm") or raw.get("confusable") or raw.get("lookalikes")),
        "similar_meaning": norm_rel(raw.get("similar_meaning") or raw.get("similarMeaning") or raw.get("synonyms")),
    }


def merge_entries(words: list, raw_data, overwrite: bool) -> tuple:
    if isinstance(raw_data, list):
        items = raw_data
    elif isinstance(raw_data, dict) and isinstance(raw_data.get("words"), list):
        items = raw_data["words"]
    else:
        items = [raw_data]

    added = updated = skipped = 0
    for item in items:
        entry = normalize_entry(item)
        if not entry:
            continue
        idx = next((i for i, w in enumerate(words) if w.get("word", "").lower() == entry["word"].lower()), -1)
        if idx == -1:
            words.append(entry)
            added += 1
        elif overwrite:
            entry["id"] = words[idx]["id"]
            words[idx] = entry
            updated += 1
        else:
            skipped += 1

    save_words(words)
    return added, updated, skipped


# ==========================================
# メインアプリ (Flet ネイティブUI)
# ==========================================
def main(page: ft.Page):
    page.title = "My英単語帳 A-Z"
    page.bgcolor = CANVAS
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=MBLUE,
        visual_density=ft.VisualDensity.COMPACT,
    )

    state = {
        "words": load_words(),
        "letter": "ALL",
        "query": "",
    }

    clipboard = ft.Clipboard()

    def notify(msg: str):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(msg, color=MYELLOW, weight=ft.FontWeight.BOLD, size=13),
                bgcolor=INK,
                duration=2200,
            )
        )

    def sharp_button(label: str, bg: str, fg: str, on_click, icon=None, expand=False, height=40):
        row_items = []
        if icon:
            row_items.append(ft.Icon(icon, color=fg, size=16))
        row_items.append(ft.Text(label, color=fg, weight=ft.FontWeight.W_800, size=12))
        return ft.Container(
            content=ft.Row(row_items, alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            bgcolor=bg,
            border=ft.Border.all(2, INK),
            border_radius=0,
            height=height,
            padding=ft.Padding.symmetric(horizontal=10),
            on_click=on_click,
            expand=expand,
            ink=True,
        )

    # 動的UI参照
    word_count_text = ft.Text("0", size=20, weight=ft.FontWeight.W_900, color=INK)
    az_row = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO)
    list_view = ft.ListView(expand=True, spacing=12, padding=ft.Padding.only(left=12, right=12, top=10, bottom=90))

    # ==========================================
    # 詳細モーダル（単語カードタップ時）
    # ==========================================
    def open_detail_dialog(w: dict):
        body_controls = []

        # 発音・品詞・活用
        meta_chips = []
        if w.get("partOfSpeech"):
            meta_chips.append(
                ft.Container(
                    content=ft.Text(w["partOfSpeech"], size=11, weight=ft.FontWeight.W_900, color=WHITE),
                    bgcolor=INK,
                    padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                )
            )
        if w.get("phonetic"):
            meta_chips.append(ft.Text(w["phonetic"], size=12, color=MUTED, weight=ft.FontWeight.W_600))
        if meta_chips:
            body_controls.append(ft.Row(meta_chips, wrap=True, spacing=8))

        if w.get("inflections"):
            body_controls.append(
                ft.Container(
                    content=ft.Text(f"活用・変化: {w['inflections']}", size=12, color=INK, weight=ft.FontWeight.W_600),
                    bgcolor=CANVAS,
                    border=ft.Border.all(1.5, INK),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                )
            )

        # 意味（日・中）
        meaning_rows = []
        if w.get("meaning_ja"):
            meaning_rows.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("日", size=10, weight=ft.FontWeight.W_900, color=WHITE),
                            bgcolor=MRED,
                            border=ft.Border.all(1.5, INK),
                            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                        ),
                        ft.Text(w["meaning_ja"], size=14, weight=ft.FontWeight.W_800, color=INK, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=8,
                )
            )
        if w.get("meaning_zh"):
            meaning_rows.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("中", size=10, weight=ft.FontWeight.W_900, color=WHITE),
                            bgcolor=MBLUE,
                            border=ft.Border.all(1.5, INK),
                            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                        ),
                        ft.Text(w["meaning_zh"], size=13, weight=ft.FontWeight.W_600, color=INK, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=8,
                )
            )
        if meaning_rows:
            body_controls.append(
                ft.Container(
                    content=ft.Column(meaning_rows, spacing=6),
                    bgcolor=CANVAS,
                    border=ft.Border.all(2, INK),
                    padding=10,
                )
            )

        # 例文
        examples = w.get("examples") or []
        if examples:
            body_controls.append(
                ft.Container(
                    content=ft.Text("例文・使い方", size=11, weight=ft.FontWeight.W_900, color=INK),
                    bgcolor=MYELLOW,
                    border=ft.Border.all(1.5, INK),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                )
            )
            for ex in examples:
                ex_lines = [ft.Text(ex.get("en", ""), size=13, weight=ft.FontWeight.W_800, color=INK)]
                if ex.get("ja"):
                    ex_lines.append(ft.Text(f"日: {ex['ja']}", size=12, color=INK))
                if ex.get("zh"):
                    ex_lines.append(ft.Text(f"中: {ex['zh']}", size=12, color=MUTED))
                if ex.get("note"):
                    ex_lines.append(ft.Text(f"※ {ex['note']}", size=11, color=MBLUE, weight=ft.FontWeight.W_700))
                body_controls.append(
                    ft.Container(
                        content=ft.Column(ex_lines, spacing=3),
                        border=ft.Border.only(left=ft.BorderSide(4, INK)),
                        padding=ft.Padding.only(left=10, top=4, bottom=4),
                    )
                )

        # 形が似ている語
        sim_form = w.get("similar_form") or []
        if sim_form:
            body_controls.append(
                ft.Container(
                    content=ft.Text("形が似ている語（混同注意）", size=11, weight=ft.FontWeight.W_900, color=WHITE),
                    bgcolor=MRED,
                    border=ft.Border.all(1.5, INK),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                )
            )
            for s in sim_form:
                mean_str = " / ".join(filter(None, [s.get("meaning_ja"), s.get("meaning_zh")]))
                s_lines = [
                    ft.Text(
                        f"{s.get('word', '')}  ({s.get('pos', '')})" if s.get("pos") else s.get("word", ""),
                        size=13,
                        weight=ft.FontWeight.W_900,
                        color=INK,
                    )
                ]
                if mean_str:
                    s_lines.append(ft.Text(mean_str, size=12, color=INK))
                if s.get("note"):
                    s_lines.append(ft.Text(s["note"], size=11, color=MUTED))
                body_controls.append(
                    ft.Container(
                        content=ft.Column(s_lines, spacing=2),
                        bgcolor=CANVAS,
                        border=ft.Border.all(1.5, INK),
                        padding=8,
                    )
                )

        # 意味が似ている語
        sim_mean = w.get("similar_meaning") or []
        if sim_mean:
            body_controls.append(
                ft.Container(
                    content=ft.Text("意味が似ている語（類義語）", size=11, weight=ft.FontWeight.W_900, color=WHITE),
                    bgcolor=MBLUE,
                    border=ft.Border.all(1.5, INK),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                )
            )
            for s in sim_mean:
                mean_str = " / ".join(filter(None, [s.get("meaning_ja"), s.get("meaning_zh")]))
                s_lines = [
                    ft.Text(
                        f"{s.get('word', '')}  ({s.get('pos', '')})" if s.get("pos") else s.get("word", ""),
                        size=13,
                        weight=ft.FontWeight.W_900,
                        color=INK,
                    )
                ]
                if mean_str:
                    s_lines.append(ft.Text(mean_str, size=12, color=INK))
                if s.get("note"):
                    s_lines.append(ft.Text(s["note"], size=11, color=MUTED))
                body_controls.append(
                    ft.Container(
                        content=ft.Column(s_lines, spacing=2),
                        bgcolor=CANVAS,
                        border=ft.Border.all(1.5, INK),
                        padding=8,
                    )
                )

        def on_edit(_):
            page.pop_dialog()
            open_edit_dialog(w)

        def on_delete(_):
            state["words"] = [x for x in state["words"] if x.get("id") != w.get("id")]
            save_words(state["words"])
            page.pop_dialog()
            refresh_ui()
            notify(f"「{w.get('word', '')}」を削除しました")

        dlg = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=0),
            bgcolor=WHITE,
            title=ft.Row(
                [
                    ft.Text(w.get("word", ""), size=20, weight=ft.FontWeight.W_900, color=INK, expand=True),
                    ft.IconButton(ft.Icons.CLOSE, icon_color=INK, on_click=lambda _: page.pop_dialog()),
                ]
            ),
            content=ft.Container(
                width=420,
                height=440,
                content=ft.Column(body_controls, scroll=ft.ScrollMode.AUTO, spacing=10),
            ),
            actions=[
                sharp_button("編集", MYELLOW, INK, on_edit, height=36),
                sharp_button("削除", MRED, WHITE, on_delete, height=36),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dlg)

    # ==========================================
    # JSON貼付モーダル（他AIのJSONを自動マージ）
    # ==========================================
    def open_json_paste_dialog(_=None):
        json_field = ft.TextField(
            multiline=True,
            min_lines=7,
            max_lines=10,
            hint_text='他AIが出力した ```json ... ``` やJSONテキストをそのまま貼り付け',
            border_color=INK,
            border_width=2,
            border_radius=0,
            bgcolor=WHITE,
            text_size=12,
        )
        overwrite_cb = ft.Checkbox(label="同じ単語がある場合は上書き更新する", value=False, active_color=MBLUE)

        async def paste_from_clip(_):
            try:
                txt = await clipboard.get()
                if txt:
                    json_field.value = txt
                    page.update()
                    notify("クリップボードから貼り付けました")
                else:
                    notify("クリップボードが空です")
            except Exception:
                notify("入力欄を長押しして貼り付けてください")

        async def copy_sample(_):
            try:
                await clipboard.set(SAMPLE_JSON)
                notify("JSONフォーマット例をコピーしました")
            except Exception:
                notify("コピーに失敗しました")

        def do_import(_):
            try:
                parsed = extract_json_from_text(json_field.value)
                added, updated, skipped = merge_entries(state["words"], parsed, overwrite_cb.value)
                page.pop_dialog()
                if added > 0 and state["letter"] != "ALL":
                    state["letter"] = "ALL"
                refresh_ui()
                notify(f"新規追加: {added}件 / 更新: {updated}件 / スキップ: {skipped}件")
            except Exception as err:
                notify(f"JSON読取エラー: {err}")

        dlg = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=0),
            bgcolor=CANVAS,
            title=ft.Text("他AIのJSONを貼り付けて追加", size=16, weight=ft.FontWeight.W_900, color=INK),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                sharp_button("貼付", MBLUE, WHITE, paste_from_clip, icon=ft.Icons.CONTENT_PASTE, expand=True, height=36),
                                sharp_button("例コピー", MYELLOW, INK, copy_sample, icon=ft.Icons.COPY, expand=True, height=36),
                            ],
                            spacing=8,
                        ),
                        json_field,
                        overwrite_cb,
                    ],
                    tight=True,
                    spacing=10,
                ),
            ),
            actions=[
                sharp_button("キャンセル", WHITE, INK, lambda _: page.pop_dialog(), height=38),
                sharp_button("取り込む", MBLUE, WHITE, do_import, height=38),
            ],
        )
        page.show_dialog(dlg)

    # ==========================================
    # バックアップ（保存/復元）モーダル
    # ==========================================
    def open_backup_dialog(_=None):
        all_json_text = json.dumps(state["words"], ensure_ascii=False, indent=2)
        backup_field = ft.TextField(
            value=all_json_text,
            multiline=True,
            min_lines=7,
            max_lines=10,
            border_color=INK,
            border_width=2,
            border_radius=0,
            bgcolor=WHITE,
            text_size=11,
        )

        async def copy_all(_):
            try:
                await clipboard.set(json.dumps(state["words"], ensure_ascii=False, indent=2))
                notify("全単語データをコピーしました（メモ帳等に保存できます）")
            except Exception:
                notify("コピーに失敗しました")

        def restore_all(_):
            try:
                parsed = extract_json_from_text(backup_field.value)
                added, updated, _ = merge_entries(state["words"], parsed, overwrite=True)
                page.pop_dialog()
                refresh_ui()
                notify(f"復元完了：新規 {added}件 / 更新 {updated}件")
            except Exception as err:
                notify(f"復元エラー: {err}")

        dlg = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=0),
            bgcolor=CANVAS,
            title=ft.Text("データ保存・復元 (JSON)", size=16, weight=ft.FontWeight.W_900, color=INK),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    [
                        ft.Text(
                            "データはスマホ内に自動保存されます。機種変更時は下のJSONをコピーして保管してください。",
                            size=12,
                            color=MUTED,
                        ),
                        backup_field,
                    ],
                    tight=True,
                    spacing=8,
                ),
            ),
            actions=[
                sharp_button("全コピー", MBLUE, WHITE, copy_all, height=36),
                sharp_button("この内容で復元", MYELLOW, INK, restore_all, height=36),
                sharp_button("閉じる", WHITE, INK, lambda _: page.pop_dialog(), height=36),
            ],
        )
        page.show_dialog(dlg)

    # ==========================================
    # 手動追加・編集モーダル
    # ==========================================
    def open_edit_dialog(word_obj=None):
        is_edit = word_obj is not None
        ex0 = (word_obj.get("examples") or [{}])[0] if is_edit else {}

        f_word = ft.TextField(label="英語の見出し語・文 *", value=word_obj.get("word", "") if is_edit else "", border_color=INK, border_radius=0, bgcolor=WHITE)
        f_ipa = ft.TextField(label="発音記号 (IPA)", value=word_obj.get("phonetic", "") if is_edit else "", border_color=INK, border_radius=0, bgcolor=WHITE, expand=True)
        f_pos = ft.TextField(label="品詞", value=word_obj.get("partOfSpeech", "") if is_edit else "", border_color=INK, border_radius=0, bgcolor=WHITE, expand=True)
        f_inf = ft.TextField(label="活用・変化形", value=word_obj.get("inflections", "") if is_edit else "", border_color=INK, border_radius=0, bgcolor=WHITE)
        f_ja = ft.TextField(label="日本語の意味 *", value=word_obj.get("meaning_ja", "") if is_edit else "", border_color=INK, border_radius=0, bgcolor=WHITE)
        f_zh = ft.TextField(label="中国語の意味", value=word_obj.get("meaning_zh", "") if is_edit else "", border_color=INK, border_radius=0, bgcolor=WHITE)
        f_ex_en = ft.TextField(label="例文 (英語)", value=ex0.get("en", ""), border_color=INK, border_radius=0, bgcolor=WHITE)
        f_ex_ja = ft.TextField(label="例文訳 (日本語)", value=ex0.get("ja", ""), border_color=INK, border_radius=0, bgcolor=WHITE)
        f_ex_zh = ft.TextField(label="例文訳 (中国語)", value=ex0.get("zh", ""), border_color=INK, border_radius=0, bgcolor=WHITE)
        f_ex_note = ft.TextField(label="使い方・注意点", value=ex0.get("note", ""), border_color=INK, border_radius=0, bgcolor=WHITE)

        def save_form(_):
            w_val = (f_word.value or "").strip()
            if not w_val:
                notify("英語の見出し語を入力してください")
                return

            examples = list(word_obj.get("examples") or []) if is_edit else []
            first_ex = {
                "en": (f_ex_en.value or "").strip(),
                "ja": (f_ex_ja.value or "").strip(),
                "zh": (f_ex_zh.value or "").strip(),
                "note": (f_ex_note.value or "").strip(),
            }
            if any(first_ex.values()):
                if examples:
                    examples[0] = first_ex
                else:
                    examples.append(first_ex)

            new_entry = {
                "id": word_obj["id"] if is_edit else f"w-{int(time.time() * 1000)}",
                "word": w_val,
                "phonetic": (f_ipa.value or "").strip(),
                "partOfSpeech": (f_pos.value or "").strip(),
                "inflections": (f_inf.value or "").strip(),
                "meaning_ja": (f_ja.value or "").strip(),
                "meaning_zh": (f_zh.value or "").strip(),
                "examples": examples,
                "similar_form": word_obj.get("similar_form", []) if is_edit else [],
                "similar_meaning": word_obj.get("similar_meaning", []) if is_edit else [],
            }

            if is_edit:
                idx = next((i for i, x in enumerate(state["words"]) if x.get("id") == word_obj["id"]), -1)
                if idx != -1:
                    state["words"][idx] = new_entry
            else:
                state["words"].append(new_entry)

            save_words(state["words"])
            page.pop_dialog()
            refresh_ui()
            notify("保存しました")

        dlg = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=0),
            bgcolor=CANVAS,
            title=ft.Text("単語・文を編集" if is_edit else "新しい単語・文を追加", size=16, weight=ft.FontWeight.W_900, color=INK),
            content=ft.Container(
                width=420,
                height=430,
                content=ft.Column(
                    [
                        f_word,
                        ft.Row([f_ipa, f_pos], spacing=8),
                        f_inf,
                        f_ja,
                        f_zh,
                        ft.Divider(color=INK, thickness=2),
                        f_ex_en,
                        f_ex_ja,
                        f_ex_zh,
                        f_ex_note,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                ),
            ),
            actions=[
                sharp_button("キャンセル", WHITE, INK, lambda _: page.pop_dialog(), height=38),
                sharp_button("保存する", MRED, WHITE, save_form, height=38),
            ],
        )
        page.show_dialog(dlg)

    # ==========================================
    # 画面描画 (A-Zバー & カードリスト)
    # ==========================================
    def on_select_letter(letter: str):
        state["letter"] = letter
        refresh_ui()

    def build_word_card(w: dict, stripe_color: str):
        ex_count = len(w.get("examples") or [])
        rel_count = len(w.get("similar_form") or []) + len(w.get("similar_meaning") or [])

        title_row = [ft.Text(w.get("word", ""), size=18, weight=ft.FontWeight.W_900, color=INK)]
        if w.get("partOfSpeech"):
            title_row.append(
                ft.Container(
                    content=ft.Text(w["partOfSpeech"], size=10, weight=ft.FontWeight.W_900, color=INK),
                    bgcolor=MYELLOW,
                    border=ft.Border.all(1.5, INK),
                    padding=ft.Padding.symmetric(horizontal=6, vertical=1),
                )
            )

        top_col = [ft.Row(title_row, wrap=True, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)]
        if w.get("phonetic"):
            top_col.append(ft.Text(w["phonetic"], size=11, color=MUTED))

        meaning_col = []
        if w.get("meaning_ja"):
            meaning_col.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("日", size=10, weight=ft.FontWeight.W_900, color=WHITE),
                            bgcolor=MRED,
                            border=ft.Border.all(1.5, INK),
                            padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                        ),
                        ft.Text(w["meaning_ja"], size=13, weight=ft.FontWeight.W_800, color=INK, expand=True),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            )
        if w.get("meaning_zh"):
            meaning_col.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("中", size=10, weight=ft.FontWeight.W_900, color=WHITE),
                            bgcolor=MBLUE,
                            border=ft.Border.all(1.5, INK),
                            padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                        ),
                        ft.Text(w["meaning_zh"], size=12, color=MUTED, expand=True),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            )

        card_content = ft.Column(
            [
                ft.Container(
                    content=ft.Column(top_col, spacing=3),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                    border=ft.Border.only(bottom=ft.BorderSide(2, INK)),
                ),
                ft.Container(
                    content=ft.Column(meaning_col, spacing=5),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                    border=ft.Border.only(bottom=ft.BorderSide(1.5, INK)),
                    bgcolor=WHITE,
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"例文 {ex_count}   関連語 {rel_count}", size=11, weight=ft.FontWeight.W_800, color=INK),
                            ft.Text("詳細を見る ›", size=11, weight=ft.FontWeight.W_900, color=MBLUE),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                    bgcolor=CANVAS,
                ),
            ],
            spacing=0,
            expand=True,
        )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=8, bgcolor=stripe_color, border=ft.Border.only(right=ft.BorderSide(2, INK))),
                    card_content,
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            bgcolor=WHITE,
            border=ft.Border.all(2.5, INK),
            border_radius=0,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=INK, offset=ft.Offset(4, 4)),
            on_click=lambda _, item=w: open_detail_dialog(item),
            ink=True,
        )

    def refresh_ui():
        words = state["words"]
        word_count_text.value = str(len(words))

        # A-Z バー更新
        existing = {get_initial_letter(w.get("word", "")) for w in words}
        letters = ["ALL"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if "#" in existing:
            letters.append("#")

        az_row.controls.clear()
        for l in letters:
            is_active = state["letter"] == l
            has_word = (l == "ALL") or (l in existing)
            bg = INK if is_active else (MYELLOW if (has_word and l != "ALL") else WHITE)
            fg = MYELLOW if is_active else (INK if has_word else "#999999")
            az_row.controls.append(
                ft.Container(
                    content=ft.Text(l, size=12, weight=ft.FontWeight.W_900, color=fg),
                    bgcolor=bg,
                    border=ft.Border.only(right=ft.BorderSide(2, INK)),
                    padding=ft.Padding.symmetric(horizontal=13, vertical=8),
                    on_click=lambda _, ch=l: on_select_letter(ch),
                    ink=True,
                )
            )

        # フィルタリング
        q = state["query"].strip().lower()
        filtered = []
        for w in words:
            if state["letter"] != "ALL" and get_initial_letter(w.get("word", "")) != state["letter"]:
                continue
            if q:
                blob = " ".join(
                    [
                        str(w.get("word", "")),
                        str(w.get("meaning_ja", "")),
                        str(w.get("meaning_zh", "")),
                        str(w.get("partOfSpeech", "")),
                    ]
                    + [
                        f"{e.get('en', '')} {e.get('ja', '')} {e.get('zh', '')}"
                        for e in (w.get("examples") or [])
                    ]
                ).lower()
                if q not in blob:
                    continue
            filtered.append(w)

        list_view.controls.clear()
        if not filtered:
            list_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("該当する単語がありません", size=15, weight=ft.FontWeight.W_900, color=INK),
                            ft.Text("右下の「＋ 追加」または上部の「JSON貼付」から登録してください。", size=12, color=MUTED),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    bgcolor=WHITE,
                    border=ft.Border.all(2.5, INK),
                    padding=24,
                )
            )
        else:
            groups = {}
            for w in filtered:
                l = get_initial_letter(w.get("word", ""))
                groups.setdefault(l, []).append(w)

            stripes = [MRED, MBLUE, MYELLOW]
            c_idx = 0
            for letter in sorted(groups.keys(), key=lambda x: ("~" if x == "#" else x)):
                items = groups[letter]
                list_view.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(letter, size=14, weight=ft.FontWeight.W_900, color=WHITE),
                                    bgcolor=MBLUE,
                                    width=36,
                                    height=32,
                                    alignment=ft.Alignment.CENTER,
                                    border=ft.Border.only(right=ft.BorderSide(2, INK)),
                                ),
                                ft.Container(
                                    content=ft.Text(f"INDEX / {letter}", size=11, weight=ft.FontWeight.W_900, color=INK),
                                    padding=ft.Padding.only(left=10),
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(f"{len(items)}件", size=11, weight=ft.FontWeight.W_800, color=INK),
                                    border=ft.Border.all(1.5, INK),
                                    padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                                    margin=ft.Margin.only(right=8),
                                ),
                            ],
                            spacing=0,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=WHITE,
                        border=ft.Border.all(2.5, INK),
                    )
                )
                for item in items:
                    list_view.controls.append(build_word_card(item, stripes[c_idx % 3]))
                    c_idx += 1

        page.update()

    # ==========================================
    # モンドリアン・ヘッダー（スマホ幅に最適化）
    # ==========================================
    def on_search_change(e):
        state["query"] = e.control.value or ""
        refresh_ui()

    search_field = ft.TextField(
        hint_text="英単語・日本語・中国語・例文で検索...",
        border=ft.InputBorder.NONE,
        bgcolor=WHITE,
        text_size=13,
        content_padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        on_change=on_search_change,
        expand=True,
    )

    header = ft.Container(
        bgcolor=CANVAS,
        border=ft.Border.only(bottom=ft.BorderSide(3, INK)),
        content=ft.Column(
            [
                # 上段：De Stijl 非対称グリッド
                ft.Container(
                    border=ft.Border.only(bottom=ft.BorderSide(3, INK)),
                    content=ft.Row(
                        [
                            # 左：赤ブロック（タイトル）
                            ft.Container(
                                expand=6,
                                bgcolor=MRED,
                                border=ft.Border.only(right=ft.BorderSide(3, INK)),
                                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Container(width=10, height=10, bgcolor=MYELLOW, border=ft.Border.all(1.5, INK)),
                                                ft.Text("DE STIJL DICT", size=9, weight=ft.FontWeight.W_900, color=WHITE),
                                            ],
                                            spacing=6,
                                        ),
                                        ft.Text("MY VOCAB A-Z", size=19, weight=ft.FontWeight.W_900, color=WHITE),
                                        ft.Text("日・中・英 頭文字辞書", size=10, weight=ft.FontWeight.W_700, color=WHITE),
                                    ],
                                    spacing=2,
                                ),
                            ),
                            # 右：黄（語数）＋白（保存） / 下：青（JSON貼付）
                            ft.Container(
                                expand=4,
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Container(
                                                    expand=1,
                                                    bgcolor=MYELLOW,
                                                    border=ft.Border.only(
                                                        right=ft.BorderSide(2.5, INK),
                                                        bottom=ft.BorderSide(2.5, INK),
                                                    ),
                                                    padding=ft.Padding.symmetric(vertical=4),
                                                    content=ft.Column(
                                                        [
                                                            word_count_text,
                                                            ft.Text("WORDS", size=8, weight=ft.FontWeight.W_900, color=INK),
                                                        ],
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                        spacing=0,
                                                    ),
                                                ),
                                                ft.Container(
                                                    expand=1,
                                                    bgcolor=WHITE,
                                                    border=ft.Border.only(bottom=ft.BorderSide(2.5, INK)),
                                                    padding=ft.Padding.symmetric(vertical=6),
                                                    on_click=open_backup_dialog,
                                                    ink=True,
                                                    content=ft.Column(
                                                        [
                                                            ft.Icon(ft.Icons.SAVE_ALT, size=18, color=INK),
                                                            ft.Text("保存", size=9, weight=ft.FontWeight.W_900, color=INK),
                                                        ],
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                        spacing=1,
                                                    ),
                                                ),
                                            ],
                                            spacing=0,
                                        ),
                                        ft.Container(
                                            bgcolor=MBLUE,
                                            padding=ft.Padding.symmetric(vertical=10),
                                            on_click=open_json_paste_dialog,
                                            ink=True,
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.ASSIGNMENT_ADD, size=15, color=WHITE),
                                                    ft.Text("JSON貼付", size=11, weight=ft.FontWeight.W_900, color=WHITE),
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=5,
                                            ),
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ),
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                ),
                # 検索バー
                ft.Container(
                    bgcolor=WHITE,
                    border=ft.Border.only(bottom=ft.BorderSide(2.5, INK)),
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.SEARCH, size=18, color=INK),
                                width=40,
                                height=40,
                                alignment=ft.Alignment.CENTER,
                                border=ft.Border.only(right=ft.BorderSide(2, INK)),
                            ),
                            search_field,
                        ],
                        spacing=0,
                    ),
                ),
                # A-Z バー
                ft.Container(bgcolor=WHITE, content=az_row),
            ],
            spacing=0,
        ),
    )

    # 右下フローティング追加ボタン（De Stijl 角型）
    fab = ft.Container(
        right=14,
        bottom=18,
        bgcolor=MRED,
        border=ft.Border.all(2.5, INK),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=INK, offset=ft.Offset(4, 4)),
        padding=ft.Padding.symmetric(horizontal=16, vertical=11),
        on_click=lambda _: open_edit_dialog(None),
        ink=True,
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ADD, size=18, color=WHITE),
                ft.Text("追加", size=14, weight=ft.FontWeight.W_900, color=WHITE),
            ],
            spacing=5,
        ),
    )

    root_layout = ft.SafeArea(
        expand=True,
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Column([header, list_view], spacing=0, expand=True),
                fab,
            ],
        ),
    )

    page.add(root_layout)
    refresh_ui()


if __name__ == "__main__":
    ft.run(main)
