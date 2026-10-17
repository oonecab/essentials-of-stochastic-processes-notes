# T032：最终评估修复验收

关联 [I032](../issues/I032-final-assessment-repairs.md)。

- 发布：unpack、rsync、rename、journal、switch 至少五个实际 SIGKILL 点；重启恢复后 current 只指向完整版本。持久化顺序由独立故障模型验证，不能将模型称为真实断电实验。
- journal：截断 JSON 的只读诊断、显式选择已验证版本恢复、原子替换、正常恢复/回滚/队列幂等。
- 构建：全部公开 HTML 离线，保留正式页指纹；DOM 标签/属性/顺序变异与悬空锚点必须失败；新增页/书空跑与动态页数。
- 浏览器：1800/1440/1024/390、no-JS 1440/390，全公开 HTML；CSP 实际响应与脚本失败注入。
- 权限：root 安装边界、发布身份无 release 写权限；cleanup 保留 current/恢复引用，空间/inode 门限，元数据与证据关系。
- 教材：原书扫描定位、定理逐步证明、陈述来源标识、例子分级、具体题目核对记录；C/Python 非法输入及多字段变异。
- 统一：工作单列出的构建、parity、offline、项目及测度书完整检查、发布验证；每类证据保留其真实范围。

执行结果随各批追加。未实机运行的服务器安全步骤保留为运维待执行。

## 发布耐久性批次

新增回归先因缺失 durability 模块失败，完成实现后 5 个文件/目录屏障与原子写单测通过。`tools/test_static_publish.py --release-dir deploy/portal-releases/20261017T174039` 的 21 项演练通过（`tmp/publish-check/20261017T174039-4k2i7xfp/report.json`）：六个实际 SIGKILL 点、截断 journal 只读诊断与显式恢复、后续发布、既有并发/回滚/幂等回执、真实临时 Nginx HTTPS 与 298 个直接响应文件、15 个旧入口和 PDF Range。目录 rename 前将顶层目录设为 0555 在 macOS 失败；已改为先持久化内容、rename 后锁定并同步目录，再持久化父目录。落盘失败使用 fsync 错误及顺序模型，未声称物理服务器断电实测。
