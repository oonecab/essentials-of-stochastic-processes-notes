# T011：CS:APP PDF 跳转验收

状态：completed_locally；关联 [I011](../issues/I011-csapp-pdf-navigation.md)。

静态层：12 章首、序言及各来源/习题的页序与原书清单一致；构建收录 PDF 时链接保留，关闭时转页码文字；随机过程原链接不变。

集成层：包内 PDF SHA-256 与原来源一致，PDF MIME、Range 与内容字节一致。13 个 CSAPP 维护 HTML 和全部教学源码不变，第 6 章仅修正两处节首来源链接和显示起始页，因此不重复执行与本次无关的全部算法实验；运行全仓快速检查与构建层回归。

阅读层：在本地构建包实际点击代表章首及习题 PDF 链接，核对阅读器实际页序与页上标题，返回笔记；检查桌面/窄屏链接可见可操作。浏览器不支持内嵌阅读时如实记录，不用 URL 哈希独自证明实际定位。

证据目录：`tmp/csapp/pdf-navigation/`。当前无线上部署。

## 执行证据

`tools/test_reader_views.py` 的 5 组回归已登记到根 `check` 命令：14 个章首/前置入口、习题多来源页、关闭收录的文字转换、随机过程不受影响、117 个大节首与独立来源清单的交叉核对。旧 API 失败记录保留；模拟“已收录仍转文字”的错误实现检出 15 个子用例，修前第 6 章快照精确检出 6.3 的 647≠646、6.4 的 652≠651。当前全部通过，报告 `reader-views-test-after.json`；失败证据见同目录 `reader-views-test-before.json`、`reader-views-test-mutation.json`、`section-page-links-before.json`。

`python3 tools/project.py check --quick` 通过，报告 `tmp/project-check/20261014T221214-soi4soo2/report.json`。原书 PDF 646、651 页已渲染并人工查看，分别确认印刷 645 页底部的 6.3、印刷 650 页底部的 6.4 标题；两处仅修改来源页码与 href，原文和程序不变。

QA 包 `20261014T221113` 已接受独立复核：14 页全部 780 个 PDF href 按顺序与维护页逐项相同；12 章、序言、地图首链接与来源清单相符；PDF 为 6,765,790 字节，SHA-256 `dcd44c5dd0819af7dbef3ebef088a5012aadb5c82761e4b6603b4fb5d0ff504a`，与原件逐字节相同。相对上一包 `20261014T214609`，随机过程 53 文件、Weiss 18 文件字节全部不变。证据 `package-audit.json`。

在 ego-browser 的桌面 Chromium 实际点击并查看：第 10 章 → PDF 926，阅读器显示 Chapter 10 System-Level I/O；6.3 → PDF 646，页上显示印刷 645 与 6.3 标题；390px 点击 6.4 → PDF 651，显示印刷 650 与 6.4 标题；习题 2.85 → PDF 174，显示印刷 173 与原题 2.85。已查看 7 张浏览器截图，具体文件和路径在 `browser-review.json`。第 6 章 1440px/390px 的来源文字清晰可点击，390px 整页横向溢出为 0。

390px 时原生 PDF 阅读器隐藏页码输入框，不能用该控件断言失败代替页面检查；已核对实际印刷页及标题，再把同一个阅读器加宽，确认页码仍为 651。工具中的 `Meta+[` 没有触发后退，改用浏览器真实历史条目的 `Page.navigateToHistoryEntry` 成功返回第 10 章，未声称该快捷键成功。PDF 缩放、页码片段支持仍由各浏览器实现；本轮未验证实体 iOS/Android 设备。浏览器工作空间已结束。

文档同步：source_manifest、书级 README/agent/notes README、TECH、部署说明以及 I/P/M/T011。第 6 章和汇总审阅追加 `pdf_navigation_revision` 保存旧/新页哈希和限定范围；原有程序验证继续绑定未改源码，I010/F5 保持待验收。本轮未改变计算规则、核心技术栈、服务或持久环境配置。

最终包与集成：`python3 tools/project.py build` 生成 `deploy/portal-releases/20261014T221718/`，233 个文件、52 个 HTML、36 个阅读页、5159 个本地引用通过。归档 SHA-256 为 `a0444e77d638713d24ff7f69f62346fe608ae35d6147f707c4830c653ad2eda2`。它与已实际验读的 QA 包仅有 4 份审阅 JSON 差异，HTML/PDF/CSS/JS/教学源码字节相同，见 `release-binding.json`。

记录写回后的全仓 `check --quick` 再次通过：`tmp/project-check/20261014T221844-oj8u4d9y/report.json`。`verify-release --release-id 20261014T221718` 通过，核对 230 个文件、9 个入口跳转；两本原书 PDF 的 MIME/完整哈希均正确，Range 都返回 206，32–63 字节与包内原件一致，Content-Range 总长度也一致。报告 `tmp/release-check/20261014T221718-ji9owye_/https-verification.json`；临时 Nginx 已停止。
