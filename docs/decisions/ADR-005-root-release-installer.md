# ADR-005：由 root 安装器持有静态发布树

日期：2026-10-17。状态：已接受（仓库模板；生产应用待运维）。依据：[I032](../../issues/I032-final-assessment-repairs.md) P1-6。

I029 的 release 虽为 0555/0444，但属主 reading-notes 可以 chmod。新模板将 /srv/reading-notes、releases 及已安装文件交给 root，reading-notes 只直接写私有队列。root 拥有且不可被发布用户修改的 reading-notes-publish 只接受固定动作及版本 ID；对队列使用目录 FD、O_NOFOLLOW 和受限文件集复制到 root 私有快照，再运行带白名单、哈希、持久化屏障及排他锁的发布器。

Nginx 配置仍由管理员审查。固定 nginx helper 用 systemd transient root unit 执行配置检查，然后重载 Nginx，避免发布 unit 获得整个 /var/log/nginx 的可写挂载。发布 unit 保留严格系统保护、/run/nginx.pid 的精确例外和受限安装器 sudo；release 的实际写权限由 root 属主边界保证。

采用 Unix 属主权限，不使用 chattr 不可变位；管理员可正常回滚、清理和轮换证书。保留 current、最近三个版本、最近成功发布的前版以及 journal 引用；删除需管理员显式 apply，版本最小保留七天。生产转换前备份服务/权限清单并验证 key 会话，命令见运维交接。历史 I029/I031 实机证据不改写为新模板已上线。
