# Chinese Bitmap Font Generator

This Python tool generates grid-based Chinese character images and matching `.ini` metadata, ideal for bitmap font usage in games, embedded systems, or custom UI displays.

## Features

- Outputs 512×512 PNG images (16×16 grid, each cell 32×32 pixels)
- Transparent background
- White-to-gray vertical gradient fill inside each character
- Solid black outline around each character
- Each image contains 256 characters
- `.ini` file includes line-by-line character mapping in sections like `[kanji-jis215]`

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
- Pillow library

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

## Example `.ini` Format

```
[kanji-jis215]
line 0=一丁七三上下不與
line 1=主乃久之也五井亙...
...
```

## Notes

- Character rendering is based on the provided font file.
- You can adjust `FONT_FILE`, `FONT_SIZE`, and gradient depth in the script for custom output.
