# Chinese Bitmap Font Generator

This Python tool generates grid-based Chinese character images and matching `.ini` metadata, ideal for bitmap font usage in games, embedded systems, or custom UI displays.

## Features

- Outputs 512×512 PNG images (16×16 grid, each cell 32×32 pixels)
- Transparent background
- White-to-gray vertical gradient fill inside each character
- Solid 2 px black outline around each character
- Each image contains 256 characters
- `.ini` file includes line-by-line character mapping in sections like `[kanji-jis215]`
- Glyph size and position match the existing CyberiaStyle 6 kanji pages (`kanji-jis101`–`kanji-jis214`)

## Glyph alignment

Every character is drawn on the same baseline and centered on its advance width,
so short or flat characters (`一`, `二`, `口`, `小`) stay at the same height as the rest.
(Older versions centered each character on its own ink box, which moved about 690 of the 4808 characters 1–5 px up or down.)

The size and outline were fitted against the 4126 characters that also exist in the theme's own kanji pages
(average edge difference is about 0.5 px; the outline is about 2 px wide like the theme's):

| Setting | Value | Meaning |
| --- | --- | --- |
| `FONT_SIZE` | 20 | font size in px (sets the glyph width) |
| `Y_SCALE` | 0.96 | vertical scale; the theme's kanji are slightly wider than tall |
| `BASELINE_Y` | 23 | row of the 32 px cell where the font baseline sits |
| `X_CENTER` | 15.5 | column of the cell where the middle of the character's width sits |
| `OUTLINE_WIDTH` | 2.0 | black outline width in px |
| `SUPERSAMPLE` | 8 | glyphs are drawn 8× larger and scaled down, which allows fractional sizes and the vertical scale |

The outline is grown on the enlarged drawing (at 4×) and then scaled down.
Growing it on the final 32 px cell makes it lighter wherever a stroke edge falls between two pixels,
and since that differs from character to character, the outline looked uneven.

These values assume the theme's `[common]` settings for `_japanese 16px` (`Top=8`, `Baseline=23`, `DefaultWidth=19`).
With `DefaultWidth=19` the game only draws columns 4–26 of each cell (centered on 15.5), so keep glyphs inside that range if you change the size.

## Folder Structure

```
your_project/
├── main.py
├── SourceHanSansHK-Medium.otf    # Required font file
├── edu4808.txt                   # List of Chinese characters (one line)
├── output_rgba_gradient_fixed/  # Generated images and ini file
```

## Requirements

- Python 3.7 or above
- Pillow 8.0 or above

Install dependencies:

```
pip install pillow
```

## Usage

1. Download and extract `SourceHanSansHK-Medium.otf` from the official Source Han Sans GitHub:
   https://github.com/adobe-fonts/source-han-sans/releases

2. Place your desired character list into `edu4808.txt` (each line can contain multiple characters)

3. Run the generator script:

```
python main.py
```

4. PNG font sheets and `_japanese 16px [kanji-jis] 16x16.ini` will appear in the output folder.

## Installing into CyberiaStyle 6

1. Copy the PNG files into `Themes/CyberiaStyle 6 -consciousness to cyber-/Fonts/`.
2. Append the `[kanji-jis215]` … `[kanji-jis233]` sections of the generated `.ini` to the end of `Fonts/_japanese 16px.ini`.
   - Do not copy `[common]`; the theme already has it.
   - Do not put the generated `.ini` file itself into `Fonts/`: the game only allows one `.ini` per font and stops with "More than one INI found".
3. Pages are loaded in file name order, so these pages replace the theme's own glyph for any character that is in both.

## Example `.ini` Format

```
[kanji-jis215]
line 0=一丁七三上下不與
line 1=主乃久之也五井亙...
...
```

StepMania does not trim spaces around `=`, so `line 0 = ...` does not work. The script writes `line 0=...`.

## Notes

- Character rendering is based on the provided font file.
- You can adjust `FONT_FILE`, `FONT_SIZE`, `Y_SCALE`, `BASELINE_Y`, `X_CENTER`, `OUTLINE_WIDTH`, and gradient depth in the script for custom output.
