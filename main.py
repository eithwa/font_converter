from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import configparser
import math

# === 參數設定 ===
FONT_FILE = "SourceHanSansHK-Medium.otf"
GRID_SIZE = 32

# 字的大小與位置：對齊 CyberiaStyle 6 原本 kanji-jis101~214 的字（和主題重複的 4126 字逐字比對求出）
# 所有字共用同一條基線、左右依字寬置中，不依各字筆畫範圍置中，
# 否則「一、二、口、小」這類筆畫偏扁或偏小的字會上下亂跳
FONT_SIZE = 20       # 字級（px），決定字寬
Y_SCALE = 0.96       # 垂直縮放；主題原本的字略扁，1.0 = 不縮
BASELINE_Y = 23      # 字型基線在 32px 格子裡的列位置
X_CENTER = 15.5      # 字寬中心在格子裡的欄位置；DefaultWidth=19 時遊戲只畫第 4~26 欄，中心是 15.5，外框才不會被裁掉一邊
OUTLINE_WIDTH = 2.0  # 黑色外框寬度（px），主題原本的字約 2px
SUPERSAMPLE = 8      # 先放大 8 倍畫再縮回，才能做小數字級、小數基線與垂直縮放
CHARS_PER_ROW = 16
ROWS_PER_IMAGE = 16
CHARS_PER_IMAGE = CHARS_PER_ROW * ROWS_PER_IMAGE

TEXT_FILE = "edu4808.txt"
OUTPUT_DIR = Path("output_rgba_gradient_fixed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INI_BASE_SECTION = "kanji-jis"
START_INDEX = 215

# === 讀取字表 ===
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    all_chars = list(dict.fromkeys([ch for line in f for ch in line.strip() if '\u4e00' <= ch <= '\u9fff']))
char_groups = [all_chars[i:i + CHARS_PER_IMAGE] for i in range(0, len(all_chars), CHARS_PER_IMAGE)]

# === 載入字型（放大 SUPERSAMPLE 倍） ===
font = ImageFont.truetype(FONT_FILE, round(FONT_SIZE * SUPERSAMPLE))

# 外框在放大 4 倍的圖上做（8 倍太慢，4 倍對 2px 外框已經夠細）
OUTLINE_SAMPLE = SUPERSAMPLE // 2
outline_rx = round(OUTLINE_WIDTH * OUTLINE_SAMPLE)
outline_ry = round(OUTLINE_WIDTH * OUTLINE_SAMPLE / Y_SCALE)  # 垂直縮放前的距離，縮放後才是圓的

# 放大後的畫布：四周留空白給外框；縮回 32x32 時取 sample_box 這塊，上下依 Y_SCALE 縮放
pad = 2 * (max(outline_rx, outline_ry) + OUTLINE_SAMPLE)
big_cell_h = GRID_SIZE * SUPERSAMPLE / Y_SCALE
big_mask = Image.new("L", (GRID_SIZE * SUPERSAMPLE + 2 * pad, math.ceil(big_cell_h) + 2 * pad), 0)
big_draw = ImageDraw.Draw(big_mask)
sample_box = (pad, pad, pad + GRID_SIZE * SUPERSAMPLE, pad + big_cell_h)
outline_box = tuple(v / 2 for v in sample_box)
# 圓形外框每一列往左右擴的寬度
outline_widths = [int(outline_rx * math.sqrt(max(0.0, 1 - (dy / outline_ry) ** 2)))
                  for dy in range(-outline_ry, outline_ry + 1)]


def render_masks(char):
    """回傳 (字的遮罩, 外框遮罩)，都是 GRID_SIZE x GRID_SIZE。"""
    big_draw.rectangle((0, 0) + big_mask.size, fill=0)
    # anchor "ms"：x 是字寬的中心、y 是基線，所有字都用同一個點
    big_draw.text((pad + X_CENTER * SUPERSAMPLE, pad + BASELINE_Y * SUPERSAMPLE / Y_SCALE),
                  char, font=font, fill=255, anchor="ms")
    fill = big_mask.resize((GRID_SIZE, GRID_SIZE), Image.BOX, box=sample_box)

    # 外框：在放大的圖上把字往外擴 OUTLINE_WIDTH 再縮回。
    # 不能在 32x32 上擴：筆畫邊緣常落在像素中間（半透明），擴出來的外框就會變淡，而且每個字深淺不同
    small = big_mask.reduce(2)
    widened = [small]
    for w in range(1, outline_rx + 1):
        widened.append(ImageChops.lighter(widened[-1], ImageChops.lighter(
            ImageChops.offset(small, w, 0), ImageChops.offset(small, -w, 0))))
    grown = small
    for dy, w in zip(range(-outline_ry, outline_ry + 1), outline_widths):
        grown = ImageChops.lighter(grown, ImageChops.offset(widened[w], 0, dy))
    outline = grown.resize((GRID_SIZE, GRID_SIZE), Image.BOX, box=outline_box)
    return fill, outline


# 建立漸層圖（白 → 較亮的灰），每個字都一樣，只需建一次
gradient = Image.new("L", (GRID_SIZE, GRID_SIZE))
for gy in range(GRID_SIZE):
    gray = int(255 - (gy / (GRID_SIZE - 1)) * 64)  # 255 → 191
    ImageDraw.Draw(gradient).line([(0, gy), (GRID_SIZE, gy)], fill=gray)

# === 準備 ini 結構 ===
# [common] 跟 CyberiaStyle 6 的 _japanese 16px.ini 一樣（字是照這組設定排的）；
# 合併進主題 ini 時只需要加 [kanji-jis215] 之後的區段
config = configparser.ConfigParser()
config.optionxform = str
config["common"] = {
    "Top": "8",
    "Baseline": "23",
    "LineSpacing": "23",
    "TextureHints": "grayscale 16bpp",
    "DefaultWidth": "19"
}

# === 產圖迴圈 ===
for group_idx, group in enumerate(char_groups):
    index = START_INDEX + group_idx
    section_name = f"{INI_BASE_SECTION}{index}"
    file_name = f"_japanese 16px [{section_name}] 16x16"

    img = Image.new("RGBA", (CHARS_PER_ROW * GRID_SIZE, ROWS_PER_IMAGE * GRID_SIZE), (0, 0, 0, 0))
    ini_section = {}

    for i, char in enumerate(group):
        row, col = divmod(i, CHARS_PER_ROW)
        x = col * GRID_SIZE
        y = row * GRID_SIZE

        # 建立遮罩
        mask, outline_mask = render_masks(char)

        # 套用遮罩產生漸層文字
        colored = Image.merge("RGBA", (gradient, gradient, gradient, mask))

        # 建立黑邊圖
        border_img = Image.new("RGBA", (GRID_SIZE, GRID_SIZE), (0, 0, 0, 0))
        border_img.paste((0, 0, 0, 255), (0, 0), outline_mask)

        # 貼到主圖
        img.alpha_composite(border_img, (x, y))
        img.alpha_composite(colored, (x, y))

        # ini 記錄
        ini_section.setdefault(f"line {row}", "")
        ini_section[f"line {row}"] += char

    # 儲存 PNG 與 INI 區段
    img.save(OUTPUT_DIR / f"{file_name}.png")
    config[section_name] = ini_section

# === 儲存 .ini 檔 ===
# StepMania 讀 ini 不會去掉等號兩邊的空白，「line 0 = ...」會讀不到列號，所以等號兩邊不能有空白
with open(OUTPUT_DIR / "_japanese 16px [kanji-jis] 16x16.ini", "w", encoding="utf-8") as f:
    config.write(f, space_around_delimiters=False)

print(f"✅ 所有圖與 INI 已輸出到：{OUTPUT_DIR}")
