"""
底層 PNG 影像逆向工程解碼器 (png_decoder.py)
零第三方套件依賴，僅使用 Python 標準庫 (struct, zlib, zipfile) 直接解析 PNG IHDR 與 IDAT 資料塊，
完整實作 RFC 2083 PNG Scanline 濾波還原演算法 (None, Sub, Up, Average, Paeth)，
自動將 575x313 像素畫布轉譯為 9x5 色彩符號矩陣與精確 Hex 色票。
"""

from dataclasses import dataclass
import os
import struct
from typing import Dict, List, Tuple
import zipfile
import zlib


@dataclass(frozen=True)
class DecodedGridImage:
    """PNG 解碼後之網格影像資訊與符號矩陣。"""
    width: int
    height: int
    bit_depth: int
    color_type: int
    rows: int
    cols: int
    symbol_grid: Tuple[Tuple[str, ...], ...]
    hex_grid: Tuple[Tuple[str, ...], ...]
    palette_map: Dict[str, str]


def _paeth_predictor(a: int, b: int, c: int) -> int:
    """RFC 2083 標準 Paeth 濾波預測器。"""
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _classify_rgb_to_symbol(r: int, g: int, b: int) -> str:
    """將 RGB 像素值映射為 R (紅)、Y (黃)、G (綠)、B (藍) 四色代號。"""
    if r > 200 and g < 50 and b < 50:
        return "R"
    if r > 200 and g > 150 and b < 50:
        return "Y"
    if g > 140 and r < 150:
        return "G"
    return "B"


def ensure_image_extracted(
    target_png_path: str,
    fallback_pptx_path: str,
) -> str:
    """確保 PNG 圖檔存在；若尚未擷取則自動從原始 PPTX 壓縮結構中提取 ppt/media/image1.png。"""
    if os.path.exists(target_png_path):
        return target_png_path

    if os.path.exists(fallback_pptx_path):
        os.makedirs(os.path.dirname(target_png_path), exist_ok=True)
        with zipfile.ZipFile(fallback_pptx_path, "r") as zf:
            img_bytes = zf.read("ppt/media/image1.png")
            with open(target_png_path, "wb") as f:
                f.write(img_bytes)
        return target_png_path

    raise FileNotFoundError(
        f"找不到圖檔 {target_png_path!r} 與原始簡報 {fallback_pptx_path!r}"
    )


def decode_grid_from_png(
    png_path: str,
    grid_rows: int = 9,
    grid_cols: int = 5,
) -> DecodedGridImage:
    """
    從 PNG 二進位檔案直接解碼像素並取樣還原 9x5 色彩矩陣。
    """
    with open(png_path, "rb") as f:
        png_bytes = f.read()

    if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("非標準 PNG 檔案標頭")

    pos = 8
    width = height = bit_depth = color_type = 0
    idat_chunks: List[bytes] = []

    while pos < len(png_bytes):
        length = struct.unpack(">I", png_bytes[pos : pos + 4])[0]
        chunk_type = png_bytes[pos + 4 : pos + 8].decode("latin1")
        chunk_data = png_bytes[pos + 8 : pos + 8 + length]
        pos += 12 + length

        if chunk_type == "IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == "IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == "IEND":
            break

    raw_data = zlib.decompress(b"".join(idat_chunks))

    # color_type == 6 代表 RGBA (每像素 4 Bytes)，color_type == 2 代表 RGB (每像素 3 Bytes)
    bpp = 4 if color_type == 6 else 3
    stride = width * bpp
    reconstructed_rows: List[List[int]] = []
    prev_row = [0] * stride
    offset = 0

    for _ in range(height):
        filter_type = raw_data[offset]
        offset += 1
        row = list(raw_data[offset : offset + stride])
        offset += stride

        if filter_type == 1:  # Sub
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev_row[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                up = prev_row[i]
                row[i] = (row[i] + ((left + up) >> 1)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev_row[i]
                c = prev_row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + _paeth_predictor(a, b, c)) & 0xFF

        prev_row = row
        reconstructed_rows.append(row)

    symbol_matrix: List[Tuple[str, ...]] = []
    hex_matrix: List[Tuple[str, ...]] = []
    palette_map: Dict[str, str] = {}

    for r in range(grid_rows):
        sym_row: List[str] = []
        hex_row: List[str] = []
        y = int((r + 0.5) * height / grid_rows)
        for c in range(grid_cols):
            x = int((c + 0.5) * width / grid_cols)
            px_offset = x * bpp
            red = reconstructed_rows[y][px_offset]
            green = reconstructed_rows[y][px_offset + 1]
            blue = reconstructed_rows[y][px_offset + 2]

            hex_code = f"#{red:02X}{green:02X}{blue:02X}"
            sym = _classify_rgb_to_symbol(red, green, blue)
            sym_row.append(sym)
            hex_row.append(hex_code)
            palette_map[sym] = hex_code

        symbol_matrix.append(tuple(sym_row))
        hex_matrix.append(tuple(hex_row))

    return DecodedGridImage(
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
        rows=grid_rows,
        cols=grid_cols,
        symbol_grid=tuple(symbol_matrix),
        hex_grid=tuple(hex_matrix),
        palette_map=palette_map,
    )

