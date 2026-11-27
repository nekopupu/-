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
# メインアプリ (Flet 1.x ネイティブUI)
# 6.78インチ (2780x1240) ＆ 中華系OS (ColorOS/HyperOS/OriginOS/MagicOS) 対応
# ==========================================
def main(page: ft.Page):
    page.title = "My英単語帳 A-Z"
    page.bgcolor = CANVAS
    page.padding = 0
    page.spacing = 0
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
    word_count_text = ft.Text("0", size=19, weight=ft.FontWeight.W_900, color=INK)
    az_row = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    list_view = ft.ListView(
        expand=True,
        spacing=12,
        padding=ft.Padding.only(left=12, right=12, top=10, bottom=96),
    )

    # ==========================================
    # 詳細モーダル（単語カードタップ時）
    # ==========================================
    def open_detail_dialog(w: dict):
        body_controls = []

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
            title=ft.Row
