很多时候我想把笔记以文本形式发给 ai，但 yuque 的导出好像有点问题。我来写几个富文本和图。

折叠块：

<details class="lake-collapse"><summary id="u3facf0b7"><span class="ne-text">hi</span></summary><p id="ue84cb787" class="ne-p"><span class="ne-text">good</span></p></details>
代码块：

```c
include
```
组合：
<details class="lake-collapse"><summary id="u07764780"><span class="ne-text">hi</span></summary><pre data-language="plain" id="Hlrhl" class="ne-codeblock language-plain"><code>ggt</code></pre><p id="u3bcae79d" class="ne-p"><img src="https://cdn.nlark.com/yuque/0/2026/png/xxx/1789570662671-b13a4ea8-62f4-412b-8afc-93bef57b1828.png" width="244" id="jCvj9" class="ne-image"><span class="ne-text">2</span></p></details>
| 11 | 12 |
| --- | --- |
| 21 | 22 |


![](https://cdn.nlark.com/yuque/0/2026/png/xxx/1789570662671-b13a4ea8-62f4-412b-8afc-93bef57b1828.png)

$ J v_k = J(v_R + v_N) = J v_R $



应该齐了。然后试验已有的导出。很明显不能导出 doc 和 pdf，带图片了。只能 md。好像是把图片转成链接了。需要选择保留 latex 格式。

# 任务
写一个 python 程序，实现对类似 md 的清理，最后只保留文本和表。折叠与代码块里的文本或 latex 就按序保留。不清楚的提问

