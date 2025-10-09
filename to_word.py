#!/usr/bin/env python
"""to_word.py

Convert a Markdown file (containing plain text and LaTeX formulas in $...$ or $$...$$) to a DOCX
file with editable Word equations using Pandoc.

Usage:
    python to_word.py input.md [output.docx] [--font FONT]

If ``output.docx`` is omitted, the script will generate a file with the same basename as the
input file but with a ``.docx`` extension.

Requirements:
    * pypandoc (``pip install pypandoc``)
    * python-docx (``pip install python-docx``)
    * Pandoc executable installed and discoverable in PATH or downloadable via pypandoc.

"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Optional

import shutil

try:
    import pypandoc
except ImportError as exc:  # pragma: no cover
    print("缺少依赖：pypandoc。请先运行 'pip install pypandoc' 后再试。", file=sys.stderr)
    raise

# 额外依赖：python-docx
try:
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
except ImportError:
    print("缺少依赖：python-docx。请先运行 'pip install python-docx' 后再试。", file=sys.stderr)
    raise

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def _ensure_pandoc_available() -> Path:
    """保证 Pandoc 可用。

    Returns
    -------
    Path
        Pandoc 可执行文件路径。
    """
    try:
        pandoc_path = Path(pypandoc.get_pandoc_path())
        logger.debug("检测到 Pandoc: %s", pandoc_path)
        return pandoc_path
    except OSError:
        # 未检测到，尝试从 PATH 查找
        path_in_env = shutil.which("pandoc")
        if path_in_env:
            logger.debug("在 PATH 中找到 Pandoc: %s", path_in_env)
            return Path(path_in_env)

        # 尝试自动下载（pypandoc >= 1.5 支持）
        logger.info("未检测到 Pandoc，尝试自动下载...")
        try:
            pandoc_path = Path(pypandoc.download_pandoc())
            logger.info("Pandoc 已下载至 %s", pandoc_path)
            return pandoc_path
        except Exception as err:  # pragma: no cover
            logger.error("无法自动下载 Pandoc，请手动安装后重试: %s", err)
            raise RuntimeError("Pandoc 不可用，且自动下载失败。请访问 https://pandoc.org/install/ 下载安装包。")


def convert_md_to_docx(input_md: Path | str, output_docx: Optional[Path | str] = None) -> Path:
    """将 Markdown 文件转换为 DOCX。

    Parameters
    ----------
    input_md : Path | str
        输入的 Markdown 文件路径。
    output_docx : Path | str, optional
        输出的 DOCX 文件路径；若为空，则生成与输入同名的 .docx 文件。

    Returns
    -------
    Path
        生成的 DOCX 文件路径。
    """
    input_path = Path(input_md).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"找不到输入文件: {input_path}")

    if output_docx is None:
        output_path = input_path.with_suffix(".docx")
    else:
        output_path = Path(output_docx).expanduser().resolve()
        # 若指定目录而非文件名，则在目录下使用输入文件名
        if output_path.is_dir():
            output_path = output_path / input_path.with_suffix(".docx").name

    # 确保 Pandoc 可用
    # _ensure_pandoc_available()

    logger.info("开始转换: %s -> %s", input_path, output_path)
    start = time.time()

    # pypandoc 会在内部调用 Pandoc，将 LaTeX 公式转换为 OMML
    pypandoc.convert_file(
        str(input_path),
        to="docx",
        format="md",
        outputfile=str(output_path),
        extra_args=["--standalone"],
    )

    elapsed = time.time() - start
    logger.info("Pandoc 转换完成，用时 %.2f 秒", elapsed)

    # 应用默认字体
    _apply_default_font(output_path, DEFAULT_FONT)
    logger.info("默认字体已应用: %s", DEFAULT_FONT)

    return output_path


# --------------------------- 字体处理 ---------------------------
DEFAULT_FONT = "Times New Roman"


def _apply_default_font(docx_path: Path, font_name: str = DEFAULT_FONT) -> None:
    """将 DOCX 中的英文字体统一设置为指定字体。

    仅修改拉丁文字体，不影响数学公式（仍使用 Cambria Math）。
    """
    doc = Document(str(docx_path))

    # 1. 修改样式
    for style in doc.styles:
        if style.type in {WD_STYLE_TYPE.PARAGRAPH, WD_STYLE_TYPE.CHARACTER}:
            if style.font is not None:
                style.font.name = font_name

    # 2. 修改已存在的段落/Run 直接格式化
    for para in doc.paragraphs:
        for run in para.runs:
            run.font.name = font_name

    doc.save(str(docx_path))


def _parse_cli() -> tuple[Path, Optional[Path]]:
    if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    input_md = Path(sys.argv[1])
    output_docx: Optional[Path] = None
    font_arg: Optional[str] = None

    if len(sys.argv) >= 3:
        output_docx = Path(sys.argv[2])
    if len(sys.argv) >= 4:
        font_arg = sys.argv[3]

    global DEFAULT_FONT  # pylint: disable=global-statement
    if font_arg:
        DEFAULT_FONT = font_arg

    return input_md, output_docx


def main() -> None:  # pragma: no cover
    input_md, output_docx = _parse_cli()
    try:
        convert_md_to_docx(input_md, output_docx)
    except Exception as exc:
        logger.error("转换失败: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()