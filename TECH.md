# Reading Notes — 技术事实唯一来源

<!-- project-governance:managed:start -->
## 项目目的

统一管理 Durrett 随机过程与 Weiss 数据结构笔记，保留每本书的正式 HTML、可运行示例、来源与验证记录，共用阅读入口和静态发布流程。

## 项目分类

- 项目类型：`generic`
- 治理级别：`controlled`

## 技术栈基线

### 语言

- HTML / CSS / JavaScript
- 静态 MathML / SVG
- C11
- Python 3

### 框架与核心库

- Python 标准库；页面不依赖外部前端框架

### 运行时与工具链

- Python 3.10+
- Clang（C11、AddressSanitizer、UndefinedBehaviorSanitizer）
- Make
- Poppler pdftotext
- Node.js（发布脚本语法校验）
- Nginx（服务器静态 HTTPS 服务）

## 源码边界

- books/stochastic
- books/weiss
- portal
- deploy
- tools

## 架构事实

- books/catalog.json 登记书籍入口、目录和发布前缀；每本书保留一份全书总览及按章维护的独立 HTML。
- 随机过程以 code/ 下 C/Python 为维护源并同步 HTML；Weiss 教学代码以正式 HTML 为维护源，c/ 为原书图例的独立 C 实现。
- 根目录工具统一调用各书既有校验器，输出写入被忽略的 tmp/ 或 deploy/portal-releases/。
- 统一发布保留 /stochastic/ 与 /weiss/ URL；部署使用独立版本目录和 current 原子切换，同时维护本版 CSP。
- 根 Git 历史与远端沿用；原 Weiss 工作目录保留，合并后的维护入口为本仓库。

## 项目类型约束

- 明确领域边界，并在 TECH.md 中记录项目专属架构事实。

## 项目专属规则

- 修改某本书之前读取 books/<书籍>/agent.md 与 notes/README.md；专项内容标准由这些文档维护。
- 保留原书条件、题号、版本、来源页码和校注依据；静态检查和执行样本不能替代原书内容核对。
- 保留单文件 HTML 的章节顺序、锚点、离线能力与桌面/窄屏阅读行为。
- 审阅文件的历史哈希保持历史事实；改变当前文件绑定时注明范围、原因和原值。
- 新增书籍同步更新 catalog、首页、构建路由、验证与来源说明；只维护一份正式内容。
- 统一部署的操作说明以 deploy/README.md 为准；各书 deploy/ 为保留的单书工具与历史材料。
<!-- project-governance:managed:end -->

## 已确认的技术细节

每本书的实际目录和预期范围以 [books/catalog.json](books/catalog.json) 为准。源布局与发布布局分开：`books/<id>/` 保存维护源，归档使用 `<publish_prefix>/` 保持站点地址。共同命令依赖各书原检查器，不重新实现数学校验；压缩包只包含显式清单中的发布文件。各书保留原单书构建器，公共构建复用随机过程的确定性归档函数。

内容与计算规则的权威入口见 [规则职责索引](docs/rules/README.md)，兼容取舍见 [ADR-001](docs/decisions/ADR-001-book-subprojects.md)。

## 技术栈变更索引（只追加）

“技术栈变更”至少包括语言、运行时、框架、核心库、构建工具、数据库或中间件的新增、移除、替换、主版本升级，以及兼容基线变化。普通补丁升级仅在影响行为、兼容性或安全基线时记录。

| 日期 | 变更前 → 变更后 | 科学/工程理由 | 兼容、迁移与回滚影响 | 问题单 / ADR |
|---|---|---|---|---|
| 2026-10-12 | 分散笔记目录和外部 Weiss 构建来源 → 同仓库书籍子项目、统一标准库工具入口 | 一次克隆包含维护与验证所需源，保留原代码维护源 | 发布 URL 保持，原 Weiss 目录及迁移前快照保留；无新前端框架 | [I001](issues/I001-project-merge.md) / [ADR-001](docs/decisions/ADR-001-book-subprojects.md) |

> 详细论证写入问题单或 ADR；本表保存可追踪索引，不得覆盖历史记录。
