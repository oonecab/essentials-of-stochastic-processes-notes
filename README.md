# Reading Notes · 读书笔记

把一本书作为独立子项目，在同一个仓库中维护中文伴读笔记、习题解答、可运行程序、原书来源和验证记录。目前收录 Richard Durrett《Essentials of Stochastic Processes》第三版和 Mark Allen Weiss《Data Structures and Algorithm Analysis in C》第二版（中国改编版）。

统一阅读站点为 [notes.zzzping.top](https://notes.zzzping.top/)。GitHub 仓库为 [oonecab/reading-notes](https://github.com/oonecab/reading-notes)，沿用随机过程项目的 Git 历史；本地项目目录继续沿用原名。

| 子项目 | 阅读入口 | 内容与维护方式 |
|---|---|---|
| [Durrett 随机过程](books/stochastic/README.md) | [全书地图](books/stochastic/notes/book_overview.html) | 9 个 HTML 页面、236 道习题、7 组 C/Python 示例；独立源码同步到网页 |
| [Weiss 数据结构与算法](books/weiss/README.md) | [全书地图](books/weiss/notes/book_overview.html) | 13 个 HTML 页面、362 道习题、205 组双语实现；从正式 HTML 提取代码验证，另有 171 个 C 图例入口 |

## 阅读与本地运行

直接用浏览器打开上述全书地图即可离线阅读。每章是一份完整 HTML，公式、图表、正文代码和导航保存在文件内；保留完整子项目目录，相关文件链接才能正常使用。

统一书架和资料网页来自发布构建。在仓库根目录执行以下命令，预览会先构建完整站点，再仅向本机提供服务：

```sh
python3 tools/project.py doctor
python3 tools/project.py serve
```

访问 `http://127.0.0.1:8000/`，按 `Ctrl+C` 停止；端口可用 `--port 8080` 指定。已生成版本可使用 `serve --release-id YYYYMMDDTHHMMSS` 预览。原始 HTML 与发布页的样式转换分开维护，预览提供的是正式包中的页面。

Python 需要 3.10 或更高版本，项目脚本使用标准库。完整验证需要 Clang、Make 和 Poppler 的 `pdftotext`；构建还需要 Node.js 检查页面脚本。`doctor` 检查工具是否可用，不会安装软件。网页服务器只提供静态文件。

```sh
# 随机过程：编译或运行独立示例
make -C books/stochastic/code
python3 books/stochastic/code/chapter02_poisson_processes/poisson.py
./books/stochastic/code/build/poisson

# Weiss：运行全部 C 图例和 TestKit
make -C books/weiss/c check
```

## 项目结构与维护

```text
books/
  catalog.json                  # 书籍目录、入口、发布前缀与维护方式
  stochastic/                   # 随机过程：notes、code、assets、tools、review
  weiss/                        # Weiss：notes、c、原书 PDF、原图例源码包
portal/                         # 统一书架与发布阅读样式
tools/project.py                # 环境、校验、构建、预览的统一入口
deploy/                         # 统一构建、HTTPS 验证及 Nginx 模板
docs/                           # 文档职责、架构决策、环境与治理
issues/、plan/、milestone/、test/ # 问题单、实施计划、里程碑与测试设计
AGENTS.md、CLAUDE.md、TECH.md     # Agent 入口与技术事实
.project-governance.json        # 可重复生成的治理配置
```

一书一个子项目、一章一个笔记文件；保持已有章序、文件名、锚点和相对资源路径。公共层负责登记、验证、阅读入口和发布；每本书的算法与内容标准仍由自己的[维护约定](docs/rules/README.md)约束。迁入的 PDF 和原代码包用于确定教材版次与来源，验证过程中不自动替换。

修改随机过程程序后执行 `python3 books/stochastic/tools/sync_code.py --write`，再运行检查。Weiss 的教学算法直接编辑正式 HTML，再提取验证；`books/weiss/c/` 保留原图例的 C 转换，两者的职责见子项目说明。VS Code 从本仓库根目录打开，使用 `.vscode/` 中的“调试指定图例”或“调试 TestKit 指定用例”。

```sh
# 快速检查：结构、链接、代码同步、当前审阅绑定
python3 tools/project.py check --quick

# 完整检查：两本书的现有数值/功能验证与全部 C 图例
python3 tools/project.py check

# 可选按书检查，以及额外复核已登记的实验计数
python3 tools/project.py check --book stochastic
python3 tools/project.py check --book weiss --benchmarks
```

根 `Makefile` 提供 `make check`、`make check-fast`、`make build` 和 `make serve` 等快捷入口。运行日志和 JSON 证据写入 `tmp/project-check/`，提取件与二进制不纳入提交。结构、程序、原书内容复核及浏览器验收分别记录；程序执行通过不能代替全部数学论证正确性的证明。

采用 `controlled` 治理级别，以覆盖目录迁移、公共发布与恢复。详细职责入口是 [docs/README.md](docs/README.md)，当前技术事实见 [TECH.md](TECH.md)，治理更新见[操作说明](docs/governance-updates.md)，新增书籍方法见[子项目接入说明](docs/adding-a-book.md)，本次迁移及来源见[迁移记录](docs/migration-20261012.md)。

## 构建与部署

```sh
python3 tools/project.py build
# 可指定固定版本 ID；已有目录会拒绝覆盖
python3 tools/project.py build --release-id YYYYMMDDTHHMMSS
```

统一包位于 `deploy/portal-releases/<release-id>/`，构建从本仓库两本书取源，不需要外部 Weiss 目录。发布 URL 保留 `/stochastic/` 与 `/weiss/`，因此这次源码搬迁不会改变现有站点的章节地址。

包内包括站点归档、逐文件 SHA-256、版本清单和本版 CSP 对应的 Nginx 配置。服务器采用独立 `releases/<release-id>` 目录与 `current` 原子切换；回滚同时恢复站点链接与该版本的配置。完整步骤、证书维护、验收边界及回滚命令见[部署说明](deploy/README.md)。

可用 `python3 tools/project.py verify-release --release-id YYYYMMDDTHHMMSS` 在临时本地 Nginx 上验证 HTTPS 响应、文件哈希、MIME、CSP、旧入口和 PDF Range；需要本机 Nginx 与 OpenSSL。该检查不会修改系统 Nginx 配置。生产上传、生效与公网浏览器验收在明确的发布任务中执行并单独记录。
