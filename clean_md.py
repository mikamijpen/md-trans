#!/usr/bin/env python3
"""清洗类似语雀导出的 md：只保留纯文本和表格。

用法（管道过滤）：
    python clean_md.py < input.md > output.md
    type input.md | python clean_md.py > output.md
    cat input.md | python clean_md.py

规则：
- 表格原样保留（单元格内仍做链接/加粗/图片等行内清理，但保留管道结构）
- 图片（![](url) / <img>）整体丢弃，保留周围文字
- [文字](url) 只留文字；**加粗/*斜体/删除线/标题#/引用>/列表符号/分割线只留文字
- 折叠块 <details> 内按序保留：summary 标题 + 正文纯文本
- 围栏代码块 ``` / 内联 `code` / HTML <pre><code> 内容前加 [代码] 标记保留
- LaTeX $...$ / $$...$$ 原样保留（不受加粗等清理影响）
"""
import html
import re
import sys


def clean_md(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    codeblocks: list[str] = []
    inlinecodes: list[str] = []
    maths: list[str] = []
    htmlcodes: list[str] = []

    def _ph(kind: str, i: int) -> str:
        return f"\n__{kind}_{i}__\n"

    # 1. 围栏代码块 ```...``` 先占位保护
    def _fence(m: re.Match) -> str:
        codeblocks.append(m.group(1))
        return _ph("CODEBLOCK", len(codeblocks) - 1)

    text = re.sub(r"```[^\S\n]*\w*[^\S\n]*\n(.*?)```[^\S\n]*", _fence, text, flags=re.DOTALL)

    # 2. LaTeX 公式占位保护（不受后续 * _ 清理影响）
    def _math(m: re.Match) -> str:
        maths.append(m.group(0))
        return f"__MATH_{len(maths) - 1}__"

    text = re.sub(r"\$\$(.+?)\$\$", _math, text, flags=re.DOTALL)
    text = re.sub(r"(?<!\$)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", _math, text, flags=re.DOTALL)

    # 3. 行内代码 `...` 占位保护
    def _inline(m: re.Match) -> str:
        inlinecodes.append(m.group(1))
        return f"__INLINECODE_{len(inlinecodes) - 1}__"

    text = re.sub(r"`([^`\n]+?)`", _inline, text)

    # 4. HTML <pre><code>...</code></pre>（折叠块里的代码）占位，后面加 [代码] 标记
    def _htmlcode(m: re.Match) -> str:
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        htmlcodes.append(html.unescape(inner))
        return _ph("HTMLCODE", len(htmlcodes) - 1)

    text = re.sub(
        r"<pre[^>]*>\s*(?:<code[^>]*>)?(.*?)"
        r"(?:</code\s*>)?\s*</pre\s*>",
        _htmlcode,
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 5. HTML 清理：块级标签换行，图片丢弃，其余去标签留文字，按序保留
    text = re.sub(r"<img[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(
        r"</?(details|summary|p|div|pre|h\d|ul|ol|li|table|tr|td|th|blockquote)[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)

    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def inline_clean(s: str) -> str:
        stash: dict[str, str] = {}

        def _stash_math(m: re.Match) -> str:
            k = f"\x00M{len(stash)}\x00"
            stash[k] = m.group(0)
            return k

        def _stash_code(m: re.Match) -> str:
            k = f"\x00C{len(stash)}\x00"
            stash[k] = m.group(0)
            return k

        s = re.sub(r"__MATH_\d+__", _stash_math, s)
        s = re.sub(r"__INLINECODE_\d+__", _stash_code, s)
        s = re.sub(r"!\[[^\]]*?\]\([^)]*?\)", "", s)  # markdown 图片：丢弃
        s = re.sub(r"!\[[^\]]*?\]\[[^\]]*?\]", "", s)  # 引用式图片：丢弃
        s = re.sub(r"\[([^\]]*?)\]\([^)]*?\)", r"\1", s)  # [文字](url) -> 文字
        s = re.sub(r"\[([^\]]*?)\]\[[^\]]*?\]", r"\1", s)  # [文字][ref] -> 文字
        s = re.sub(r"<(https?://[^>\s]+)>", r"\1", s)  # <url> -> url
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"__(.+?)__", r"\1", s)
        s = re.sub(r"~~(.+?)~~", r"\1", s)
        s = re.sub(r"\*([^*\n]+?)\*", r"\1", s)
        s = re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"\1", s)
        s = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]+", "", s)  # 标题只留文字
        s = re.sub(r"^[ \t]{0,3}>[ \t]?", "", s)  # 引用只留文字
        s = re.sub(r"^[ \t]*[-*+][ \t]+", "", s)  # 无序列表去符号
        s = re.sub(r"^[ \t]*\d+[.)][ \t]+", "", s)  # 有序列表去符号
        for k, v in stash.items():
            s = s.replace(k, v)
        return s.strip()

    def restore_placeholders(s: str) -> str:
        s = re.sub(
            r"__MATH_(\d+)__",
            lambda m: maths[int(m.group(1))],
            s,
        )
        s = re.sub(
            r"__INLINECODE_(\d+)__",
            lambda m: "[代码] " + inlinecodes[int(m.group(1))].strip(),
            s,
        )
        return s

    def emit_code(content: str) -> None:
        content = content.strip("\n")
        if not content.strip():
            return
        if "\n" in content.rstrip():
            out.append("[代码]")
            out.extend(ln.rstrip() for ln in content.strip("\n").split("\n"))
        else:
            out.append("[代码] " + content.strip())

    table_delim = re.compile(r"^\s*\|?[\s:|-]+\|[\s|:|-]*$")

    while i < n:
        raw = lines[i]
        s = raw.strip()

        m = re.match(r"\s*__(CODEBLOCK|HTMLCODE)_(\d+)__\s*$", s)
        if m:
            idx = int(m.group(2))
            emit_code(codeblocks[idx] if m.group(1) == "CODEBLOCK" else htmlcodes[idx])
            i += 1
            continue

        # 表格块：当前行含 | 且下一行是分隔行，则连续收集团块原样保留
        if "|" in s and i + 1 < n and table_delim.match(lines[i + 1].strip()):
            while i < n and "|" in lines[i] and lines[i].strip():
                cell_line = restore_placeholders(inline_clean(lines[i].strip()))
                out.append(re.sub(r"[ \t]+", " ", cell_line).strip())
                i += 1
            continue

        if not s:
            out.append("")
            i += 1
            continue

        if re.match(r"^\s*([-*_][ \t]*){3,}\s*$", raw):  # 分割线：丢弃
            i += 1
            continue

        s = inline_clean(s)
        s = restore_placeholders(s)
        s = re.sub(r"[ \t]+", " ", s).strip()
        # 图片独占一行被删光后，不留空行占位以外的东西
        out.append(s)
        i += 1

    # 压缩多余空行：最多保留一个空行，首尾去空
    compact: list[str] = []
    blank = 0
    for ln in out:
        if ln.strip():
            compact.append(ln.rstrip())
            blank = 0
        else:
            blank += 1
            if blank <= 1:
                compact.append("")
    while compact and not compact[0].strip():
        compact.pop(0)
    while compact and not compact[-1].strip():
        compact.pop()
    return "\n".join(compact) + ("\n" if compact else "")


def main() -> None:
    data = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    sys.stdout.buffer.write(clean_md(data).encode("utf-8"))


if __name__ == "__main__":
    main()
