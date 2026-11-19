"""列出字型裡有、但 CyberiaStyle 6 還畫不出來的字，寫進 font_extra.txt。

用法：
    python make_extra_list.py "<StepMania>/Themes/CyberiaStyle 6 -consciousness to cyber-/Fonts"

main.py 會把 font_extra.txt 的字接在 edu4808.txt 後面產生字頁。
主題原本就有的字（kanji-jis101~214、_jp 16px 等）不重做，遊戲裡看起來跟以前一樣。
"""
from pathlib import Path
import re
import sys
import unicodedata

from fontTools.ttLib import TTFont
from PIL import ImageFont

FONT_FILE = "SourceHanSansHK-Medium.otf"
TEXT_FILE = "edu4808.txt"
OUTPUT_FILE = "font_extra.txt"
FIRST_OWN_PAGE = 215  # kanji-jis215 之後是這個工具產生的頁，不算主題原本的字
TOP_FONT = "Common default"  # 遊戲裡每個字型都會先載入它，它再 import 中日韓字型

# 不要的字元類別：控制字元、格式字元、私用區、空白、組合用符號
SKIP_CATEGORIES = {"Cc", "Cf", "Cs", "Co", "Cn", "Zs", "Zl", "Zp", "Mn", "Mc", "Me"}


def read_ini(path):
    """回傳 {區段: [(key, value), ...]}，跟遊戲一樣不去掉等號兩邊的空白。"""
    sections = {}
    current = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("[") and line.rstrip().endswith("]"):
            current = sections.setdefault(line.strip()[1:-1], [])
        elif current is not None and "=" in line:
            key, value = line.split("=", 1)
            current.append((key, value))
    return sections


def font_files(fonts_dir, name):
    """跟遊戲的 GetFontPaths 一樣：檔名以字型名稱開頭的 .ini 與 .png。"""
    files = [p for p in fonts_dir.iterdir() if p.name.lower().startswith(name.lower())]
    # 「_jp 16px」不能吃到「_jp 16pxx」：名稱後面要接空白、[ 或副檔名
    files = [p for p in files if p.name[len(name):][:1] in (" ", "[", ".")]
    inis = [p for p in files if p.suffix.lower() == ".ini"]
    pages = [p for p in files if p.suffix.lower() == ".png"]
    return (inis[0] if inis else None), pages


def page_name(png):
    m = re.search(r"\[([^\]]+)\]", png.name)
    return m.group(1) if m else "main"


def covered_chars(fonts_dir, name, seen):
    """name 這個字型（含它 import 的字型）已經畫得出來的字。"""
    if name in seen:
        return set()
    seen.add(name)
    ini_path, pages = font_files(fonts_dir, name)
    ini = read_ini(ini_path) if ini_path else {}
    chars = set()

    for key, value in ini.get("main", []):
        if key.strip().lower() == "import":
            for sub in value.split(","):
                if sub.strip():
                    chars |= covered_chars(fonts_dir, sub.strip(), seen)

    for png in pages:
        section = page_name(png)
        m = re.fullmatch(r"kanji-jis(\d+)", section)
        if m and int(m.group(1)) >= FIRST_OWN_PAGE:
            continue
        for key, value in ini.get("common", []) + ini.get(section, []):
            key = key.lower()
            if key.startswith("line "):
                chars.update(value)
            elif key.startswith("map "):
                code = key[4:]
                if code.startswith("u+"):
                    chars.add(chr(int(code[2:], 16)))
                elif len(code) == 1:
                    chars.add(code)
                # 其他是「up」「menuleft」這類別名，對應遊戲按鈕圖示，不是一般的字
            elif key.startswith("range "):
                m = re.fullmatch(r"range unicode #([0-9a-f]+)-([0-9a-f]+)", key)
                if m:
                    chars.update(chr(c) for c in range(int(m.group(1), 16), int(m.group(2), 16) + 1))
                else:
                    print(f"⚠ 沒處理的 range：{png.name} [{section}] {key}")
    return chars


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    fonts_dir = Path(sys.argv[1])
    covered = covered_chars(fonts_dir, TOP_FONT, set())
    with open(TEXT_FILE, encoding="utf-8") as f:
        covered |= {ch for line in f for ch in line.strip() if '一' <= ch <= '鿿'}

    tt = TTFont(FONT_FILE)
    full_width = tt["head"].unitsPerEm
    advances = tt["hmtx"].metrics
    pil_font = ImageFont.truetype(FONT_FILE, 64)

    extra = []
    for code, glyph_name in sorted(tt.getBestCmap().items()):
        ch = chr(code)
        # 遊戲在 Windows 上用 16 位元的 wchar_t 存字，BMP 以外的字放不進去
        if code > 0xFFFF or ch in covered:
            continue
        if unicodedata.category(ch) in SKIP_CATEGORIES:
            continue
        # 只做全形字：字頁的格子跟 DefaultWidth=19 都是照全形字排的，半形字放進去左右會空一大塊
        if advances[glyph_name][0] != full_width:
            continue
        if pil_font.getmask(ch).getbbox() is None:  # 沒有筆畫
            continue
        extra.append(ch)

    lines = ["".join(extra[i:i + 64]) for i in range(0, len(extra), 64)]
    Path(OUTPUT_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 主題已有 {len(covered)} 字；字型裡還缺 {len(extra)} 字，已寫到 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
