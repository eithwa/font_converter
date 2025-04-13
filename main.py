from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import configparser

# === 參數設定 ===
FONT_FILE = "SourceHanSansHK-Medium.otf"
FONT_SIZE = 19
GRID_SIZE = 32
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

# === 載入字型 ===
font = ImageFont.truetype(FONT_FILE, FONT_SIZE)

# === 準備 ini 結構 ===
config = configparser.ConfigParser()
config.optionxform = str
config["common"] = {
    "Top": "0",
    "Baseline": str(GRID_SIZE),
    "LineSpacing": str(GRID_SIZE),
    "DefaultWidth": str(GRID_SIZE),
    "TextureHints": "grayscale 16bpp"
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
        mask = Image.new("L", (GRID_SIZE, GRID_SIZE), 0)
        draw_mask = ImageDraw.Draw(mask)
        bbox = draw_mask.textbbox((0, 0), char, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        offset_x = (GRID_SIZE - text_w) // 2
        offset_y = (GRID_SIZE - text_h) // 2 - 6  # 原 -3，往上再 2px

        draw_mask.text((offset_x, offset_y), char, font=font, fill=255)

        # 建立漸層圖（白 → 較亮的灰）
        gradient = Image.new("L", (GRID_SIZE, GRID_SIZE))
        for gy in range(GRID_SIZE):
            gray = int(255 - (gy / (GRID_SIZE - 1)) * 64)  # 255 → 191
            ImageDraw.Draw(gradient).line([(0, gy), (GRID_SIZE, gy)], fill=gray)

        # 套用遮罩產生漸層文字
        colored = Image.merge("RGBA", (gradient, gradient, gradient, mask))

        # 建立黑邊圖
        border_img = Image.new("RGBA", (GRID_SIZE, GRID_SIZE), (0, 0, 0, 0))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx or dy:
                    offset_mask = ImageChops.offset(mask, dx, dy)
                    border_img.paste((0, 0, 0, 255), (0, 0), offset_mask)

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
with open(OUTPUT_DIR / "_japanese 16px [kanji-jis] 16x16.ini", "w", encoding="utf-8") as f:
    config.write(f)

print(f"✅ 所有圖與 INI 已輸出到：{OUTPUT_DIR}")
