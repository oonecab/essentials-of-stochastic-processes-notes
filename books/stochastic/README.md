# Durrett · 随机过程读书笔记

Richard Durrett《Essentials of Stochastic Processes》第三版的中文读书笔记，包含逐章解释、数学推导、236 道习题的题干与解答，以及七组可运行的 C11/Python 示例。

九个 HTML 页面覆盖全书地图、序言、六章正文与概率论复习附录。公式使用静态 MathML，图、样式与导航脚本保存在页面内；宽屏显示目录和阅读注解，手机可以折叠阅读。

## 阅读

克隆或下载项目后，用浏览器打开 `notes/book_overview.html`，从全书地图进入各章。也可以在本子项目根目录（`books/stochastic/`）启动本地静态服务器：

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

然后访问 <http://127.0.0.1:8000/notes/book_overview.html>。保留完整目录关系，页面中的源码下载和原书页码链接即可使用。

详细的章节范围、内容说明与复核记录见 [笔记说明](notes/README.md)。

## 示例与检查

C 程序需要支持 C11 的编译器，Python 程序仅使用标准库。在本子项目根目录（`books/stochastic/`）执行：

```sh
make -C code
python3 code/chapter02_poisson_processes/poisson.py
./code/build/poisson
```

各程序的输入与输出说明见 [代码目录](code/README.md)。完整检查需要 Python 3、clang 与 Poppler 的 `pdftotext`；部署打包还需要 Node.js 检查页面脚本。

```sh
python3 tools/sync_code.py
python3 tools/check_notes.py
python3 tools/check_review_records.py
```

检查涵盖页面结构、链接、来源页码、源码与网页的一致性、数值基准、非法输入及 ASan/UBSan。浏览器验收与数学内容的逐项复核分别保存在 `notes/` 的审阅记录中。修改程序后使用 `python3 tools/sync_code.py --write` 更新网页中的代码副本。

## 项目目录

- [notes/](notes/README.md)：阅读页面、来源清单与内容复核记录。
- [code/](code/README.md)：按章节组织的十四份 C/Python 源文件与运行说明。
- `assets/`：页面引用的原书资源。
- `tools/`：结构、内容一致性、数值与工具回归检查。
- [deploy/](deploy/README.md)：静态站点打包与 Nginx 部署说明。
- `review/`：独立复查的原始报告；后续修订及验收见 [修订记录](notes/audit_fix_review.json)。

来源：Richard Durrett, *Essentials of Stochastic Processes*, Third Edition, Springer, 2016。项目维护约定见 [agent.md](agent.md)。

主仓库提供 `python3 tools/project.py check --book stochastic` 统一检查入口，完整书架构建与发布见 [统一部署说明](../../deploy/README.md)。本子项目的 `deploy/` 保留独立随机过程包工具；日常发布使用主项目入口。
