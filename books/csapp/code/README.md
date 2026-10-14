# CS:APP 教学程序

本目录是程序的维护源，章节 HTML 保存逐字一致的阅读副本并提供下载入口。[程序索引](programs.json) 登记成组的 C/Python 实现，`additional_sources` 登记编译观察、x86-64 汇编、性能基准和官方 Y86 模拟器实验的支持文件。各程序的具体输入、输出与推导在所属章节展开。

## 运行

将所需源码放在同一实验目录，再从该目录运行。下面用临时目录保存编译结果：

```sh
csapp_run_dir="$(mktemp -d)"
clang -std=c11 -Wall -Wextra -Werror -pedantic -O1 -ffp-contract=off representation.c -o "$csapp_run_dir/representation"
"$csapp_run_dir/representation"
python3 representation.py
```

普通 C/Python 对替换文件名即可。C 检查另加 `-fsanitize=address,undefined -fno-omit-frame-pointer`。依赖标准库；按字填充和汇编的机器条件在下文单独说明。浮点例子使用 IEEE binary32/binary64、默认舍入，禁止 fast-math。

## 各章程序与计算条件

| 章节 | 程序 | 用途与边界 |
| --- | --- | --- |
| 1 | `hello`、`ch01_amdahl` | 最小输出，以及加速比的正向与反向计算；不把局部加速当作整体加速 |
| 2 | `representation`、`ch02_integer`、`ch02_float` | 定宽整数、位操作与浮点编码；Python 明确实现固定位宽并作独立数学对照 |
| 3 | `addresses`、`ch03_models`、`ch03_good_echo`、`ch03_range_check` | LP64 地址布局、状态与整数模型、单行文本读取、实际 x86-64 浮点分类；汇编需要另链接 `.S` |
| 4 | `pipeline`、`ch04_machine`、`ch04_algorithms` | 理想流水线时间、Y86 指令状态与控制条件、排序与 switch 基准；解释器验证 ISA 状态；y86/ 另提供官方 SEQ/PIPE 的 HCL 补丁与逐周期实验 |
| 5 | `reductions`、`ch05_loops`、`ch05_polynomial`、`ch05_fill` | 模 2⁶⁴ 归约与内积、复制与前缀、多项式分组、对齐填充；浮点重结合同时给出差异反例 |
| 6 | `cache`、`ch06_cache`、`ch06_kernels`、`ch06_mountain` | 明确组数、行数、块大小、替换与写策略的缓存实验；实际内存实验的条件另见第 6 章 |
| 7 | `ch07_relocation`、`ch07_archive`；`ch07_probe` 与链接/动态库支持文件 | S+A−P 和 S+A 的有限地址模型、归档成员扫描；本机链接/加载与 ELF 跨目标对象检查分别记录 |
| 8 | `ch08_ecf`、`ch08_io`、`ch08_shell` | C 使用 POSIX 进程/信号/作业控制接口，Python 给状态与顺序参考；默认运行有界自测，shell 交互须显式 `--interactive` |
| 9 | `ch09_vm`、`ch09_allocator`；`ch09_mmap.c` | 固定图 9.20 快照、有限 arena 的 8 字节教学对齐、四种合并；文件映射另在临时样本验证 |
| 10 | `ch10_rio`、`ch10_files`；`ch10_fstatcheck.c`、`ch10_cpfile.c` | 短计数/EINTR/EOF、缓冲预取、打开文件偏移与描述符继承；复制按实际字节数，包含 NUL |
| 11 | `ch11_address`、`ch11_echo`、`ch11_http` | 数值字节序、有限回环 echo、HTTP 消息边界及真实 CGI 子进程；C/Python 的具体职责另列 |
| 12 | `ch12_threads`、`ch12_models`、`ch12_sbuf`、`ch12_tfgets`、`ch12_resolver`、`ch12_servers`；`ch12_server_checks.py` | POSIX 线程、有限交错/死锁、三种超时读取、深拷贝及四种并发 Tiny 和过滤/日志代理 |

`addresses` 实际观察宿主 C/ctypes 布局，4 字节 int、8 字节 long/指针时对应 LP64。C 编译的宿主执行和 `-target x86_64-unknown-linux-gnu` 生成的静态汇编是两类证据。

`ch02_integer.py` 的 `checked_calloc` 和 `copy_elements` 同时检查本机 `size_t` 上界和 Python 容器长度上界 `sys.maxsize`。参数须为整数；非正计数、非正单项长度、乘积越界或分配引发 `MemoryError` / `OverflowError` 时返回 `None`。`copy_elements` 的调用方须提供至少 n 个源对象，每个对象至少含 size 字节；成功时依次复制这些字节。维护回归通过替换分配器核对上界和失败路径，边界测试不实际申请大缓冲区。

`pipeline` 使用三个组合逻辑延迟 300、200、400 ns 和寄存器开销 20 ns。串行通路由全部组合逻辑及一个输出寄存器组成，每项耗时 920 ns；流水线每级附有寄存器，时钟周期为 420 ns，n≥1 项的完成时间为 420(n+2) ns。样例保留 n=1、4、10，串行时间依次为 920、3680、9200 ns；五级停顿例子单独计算周期数。

`ch03_good_echo` 读取一行文本，包括长于缓冲区和 EOF 结束的最后一行。输入契约排除内嵌 NUL，读取到第一个换行后返回。`ch03_range_check` 在 x86-64 或装有 Rosetta 的 Apple Silicon macOS 上这样运行：

```sh
clang -arch x86_64 -std=c11 -Wall -Wextra -Werror -pedantic -O2 ch03_range_check.c ch03_ranges.S -o "$csapp_run_dir/ch03_range_check"
arch -x86_64 "$csapp_run_dir/ch03_range_check"
python3 ch03_range_check.py
```

默认核对 16 个边界编码；`--exhaustive` 遍历全部 2³² 个 binary32 编码。实际执行的两个汇编版本分别使用分支与条件传送。该 macOS 执行验证不等于 Linux 进程环境验证。

`ch05_fill` 的完整字存储使用 GNU/Clang `may_alias` 类型扩展；无该扩展时退回字符访问。当前条件为 8 位字节、无填充位的 unsigned long，并提供 uintptr_t。原书关于 K=sizeof(unsigned long)、起始对齐、短区域及余数的要求都在正文解释。C 的任意对象访问语义不能仅靠地址对齐来满足。

填充程序通过显式返回值和逐字节比较检查填充区与两侧保护区，失败返回 1 并输出具体位置。常规检查以 `-DNDEBUG` 再编译、执行全部 3120 例，并用写错字节的变体验证错误确实会被报告。

归约、内积、归并、前缀和多项式也先执行算法，再显式核对结果；成功用例数量从已完成检查累计。Python 的填充、进程/信号模型、I/O、作业状态、分配器和并发回归采用同样的显式失败机制。`tools/assertion_regressions.py` 在严格 C11 `-DNDEBUG` 与 Python `-O` 下实际执行，并要求故意错误的变体非零退出；断言开关不会删除这些必要动作。

`ch05_bench.c` 与 `ch05_loops.c`、`ch05_polynomial.c` 一起保存在本目录。编译命令在文件头，正文记录 scalar/no-FMA 条件、输入长度、重复次数、预热与三批时间范围，单位 ns/element。可运行的正确性检查与性能观测分别记录；重结合浮点程序仍须遵守题中误差约束。

`ch06_cache` 接受缓存配置和读写轨迹，分别统计命中、淘汰、写回与传输字节；`ch06_kernels` 覆盖非整块边长、分块转置及无向图转换；`ch06_mountain` 检查扫描次数与校验和。三者无参数运行确定性的正确性检验；后两者以 `--bench` 启动本机计时，运行条件与观测记录在第 6 章。

`ch06_cache` 的验证包括 9 条手算轨迹和 48 组固定种子轨迹。C/Python 分别对照独立的块编号、区间交集与最近访问位置模型，覆盖四种写策略组合、跨块访问、多组多路 LRU、脏块淘汰和 64 位地址上界；漏记脏位的变体须在写回用例中失败。操作数统计每条输入，命中与缺失统计每次块访问，结束时保留在缓存中的脏行不主动刷回。

`ch05_loops` 中三项分组前缀要求输入输出不相交或完全同址，允许浮点重结合；部分重叠及逐位保持串行舍入的语义在 5.19 另行说明。

`cache` 默认使用 4 组、每块 2 字节、一次访问 1 字节，支持 1、2、4 路 LRU，地址为 0—2⁶⁴−1 的十进制整数。非法输入退出 2。默认轨迹 `0,1,13,8,0` 之外，还比较 8×8、每元素 4 字节的矩阵行列访问（4 组/1 路/16 字节块、基址 0、分别冷启动）。

```sh
python3 cache.py 2 0 1 13 8 0
```

## 第二部分程序契约

`ch07_relocation` 限定 32 位地址与有符号 32 位 addend，以较宽整数计算再判断目标字段范围，错误不改输出字节。`ch07_archive` 实现原书从左到右扫描归档、归档内反复提取所需成员的规则。`ch07_probe.py` 的参数是实验输出目录，它运行真实宿主分离编译、静态归档、缺符号失败与 `dlopen`/`dlsym` 成功和失败；生成的 x86-64 ELF 对象只做静态检查。目标文件与动态库格式取决于编译目标，macOS 的宿主执行结果单独标注。

`ch08_ecf.c` 在单线程进程中观察 `fork` 私有状态、`execve`、回收、阻塞信号与 `sigsuspend`。处理函数只修改 `sig_atomic_t` 状态，并保存/恢复 `errno`；信号合并次数是当前宿主观察。Python 以事件与状态模型说明同一机制，不执行 POSIX 信号处理。`ch08_io` 的默认样例使用临时文件与受控 shell 命令；`--tfgets` 对输入给出五秒边界，流及其底层文件描述符须由调用方独占。`ch08_shell --interactive` 接受教材的空白分词、后台标记与 jobs/bg/fg；命令须给可执行文件路径，作业表以尚未回收的直属 PID 维护进程所有权。退出时先向仍登记作业的原进程组发送终止信号，再单独终止其直属 PID，最后逐一回收；这样孩子改变进程组后仍能完成清理。信号或回收失败会报告错误，不能据此声称作业已清理。

`ch09_vm` 每次都读取原书图 9.20 的同一快照，没有 TLB 回填。无参数输出四个案例；参数为一个十六进制 14 位虚拟地址。无效编码、超范围或原图未给出的 PTE 返回 2；缺页是一个已知翻译结果，并不等于输入错误。`ch09_allocator` 用 65536 字节 arena 和 8 字节教学对齐，支持 first-fit/next-fit 与已分配块保留/省略脚部；释放仅接受 NULL 或本分配器尚未释放的有效返回值。它不承诺 libc 的所有类型对齐，不用于替换系统 malloc。`ch09_mmap.c` 提供 `copy FILE` 和 `change FILE`，后者只接受精确的 `Hello, world!\n` 样本并将首字节改为 J；映射期间文件须稳定，避免并发截断。

## 第三部分程序契约

`ch10_rio` 用 8 字节教学缓冲展示预取状态；无缓冲读写循环按实际返回计数推进，遇 EINTR 重试，EOF 返回已读前缀，其余错误保留已经发生的副作用。C 的总请求长度不超过 `SSIZE_MAX`，读行容量至少 2；描述符由调用方独占并采用阻塞模式。默认的中断案例通过确定性回调注入，只验证循环行为。`--copy` 和 `--lines` 逐字节复制 stdin 或指定文件，内嵌 NUL 仍按计数传输。`ch10_files` 的默认实验仅操作自己创建的临时文件；`--list DIR` 只读目录且不承诺枚举顺序。`ch10_fstatcheck` 的数字参数必须指向当前进程已有的描述符，`read: yes` 表示所有者读权限位。`ch10_cpfile.c` 保留原图 10.5 的复制循环，编译时需同目录的 `ch10_rio.c`。

`ch11_address` 区分 16 位整数数值转换与 32 位 IPv4；默认只查询数值回环地址，显式 `hostinfo HOST` 才可能进行 DNS 查询。`ch11_echo` 的默认运行创建临时回环端口，发送分段二进制输入并半关闭写端，比较完整回声后回收服务器。`ch11_http.c` 提供有界 HTTP 解析、响应构建与描述符 I/O，并通过 `--serve-cgi ROOT [REQUESTS [CGI_PROGRAM]]` 启动真实异步 CGI：默认 fork/exec 当前二进制的 `--cgi`，也可指定可信 Python CGI 程序。父进程继续接入，CGI 独占自己的连接输出，SIGCHLD 处理器循环回收；服务进程须为单线程并独占全部子进程回收。`ch11_http.py --serve` 保留同步 CGI 参考，两条路径的用途分别说明。两种 HTTP 实验的默认输出与覆盖职责分别登记，不要求彼此输出相同。静态根目录在服务期间保持稳定，只接受简单文件名及大小受限的普通文件；HTTP 教学范围为每连接一个请求、显式消息长度和关闭连接。GET/HEAD/POST、错误响应和大小限制由正文及源码定义。字段值只剔除首尾 SP/HTAB；字段名与冒号之间的空白仍非法。完整头部须先通过消息长度和 Host 检查，再对 Expect 提前返回 417；普通 POST 必须按声明长度接收完整正文。头部决策与完整消息长度检查分别维护，代理转发继续要求完整消息。

第 12 章依赖线程的 C 程序用 `-pthread` 编译。`ch12_threads.c` 保护共享计数和有界队列，并将矩阵输出行分配给不同工作者。`--hello N` 保留线程参数直到 join，`--bench` 记录相同计算核的串行/并行宿主时间；单次时间不能推出普适加速比。`ch12_models` 在顺序程序中枚举 load/update/store 与锁的交错，不实际执行未同步的 C 共享访问。`ch12_resolver.c` 的锁和深拷贝要求所有旧接口调用遵守同一把锁，返回副本由调用方释放。

`ch12_tfgets.c` 提供 `proc`、`select`、`thread` 三种五秒输入截止时间，接受至少 2 字节的输出缓冲和由调用方独占、无未消费 stdio 缓冲的文本输入流，输入排除内嵌 NUL。无换行的 EOF 末行可返回；超时不能撤回已消费的部分输入。进程方案还要求单线程调用方独占 SIGUSR1，计时子进程由本函数独占回收，调用方不能通过 SIGCHLD 自动回收或其他 wait 抢先回收；读取结束后以 SIGKILL 取消本函数创建、尚未回收的计时子进程，再 waitpid 回收，清理挂起的通知并恢复原处理函数及掩码；取消不依赖调用者的 SIGTERM 设置。线程方案在返回前 join，避免在调用方返回后继续写入其缓冲。

`ch12_servers.c` 编译时依赖同目录 `ch11_http.c`，支持 `process`、`select`、`thread`、动态 `pool`、`echo`、`proxy` 和 `proxy-serial` 模式。监听仅绑定 `127.0.0.1`；端口 0 让系统选择临时端口，连接数限制 1—128，接收新连接的窗口为 120 秒，之后等待已接收任务结束；满队列可能推迟下次窗口检查。各连接另设等待边界，接收窗口不等于整个进程的精确退出时刻。select/echo 到达窗口后停止接入，继续处理已有客户至完成、EOF 或等待超时；其 3 秒等待期限在读到新字节时刷新。事件驱动方案把网络描述符设为非阻塞，为每个客户保存输入/输出进度；小型本地文件读取仍是同步操作。代理的转发范围为回环 HTTP GET，使用调用者指定的过滤与日志文件；这是可重复的本地协议实验，未实现通用 Internet 代理或 TLS CONNECT。运行方式、状态转换和验证边界见第 12 章。

## 官方 Y86 模拟器实验

[y86/Y86_REPRODUCE.md](y86/Y86_REPRODUCE.md) 给出 Architecture Lab 原发行包的来源哈希、GNU89/Clang 文字界面构建步骤、4.52–4.58 七个 HCL 变体、31 个程序输入，以及状态与周期比较。也可下载 [完整支持材料包](y86-verification-support.tar.gz)。官方旧 C 构建与本目录严格 C11 教学程序分别检查。普通题解的 PIPE 周期含四拍填充，官方 psim 的 CPI 周期省去这四拍；非法 push/pop 的官方 yis 与原始 SEQ/PIPE 状态差异随实验说明保留。

## 校验

`books/csapp/tools/part_two_signal_regressions.py` 直接提取第8章等待模板，验证调用前已屏蔽目标信号时的递交与原掩码恢复，并检查退出清理的进程组变化、组内剩余成员和失败路径。两类回归通过根检查入口执行，设计与证据见 [T006](../../../test/T006-csapp-part-two-review-fixes.md)。

仓库内的缓存与分配边界回归维护在 `books/csapp/tools/program_regressions.py`；本节记录维护者入口。

`tools/part_two_regressions.py` 使用独立整数与已分配区间补集/搜索游标作为参考，验证重定位以及 first-fit/next-fit 在两种尾部形式下的选址、分配失败状态保持和载荷保持，并检出错误位置符号、合并和 next-fit 游标的变异。额外执行在任务拥有的 PTY/子进程中核对作业停止、恢复、信号转发和回收；文件修改仅在测试新建的样本内发生。具体命令与阅读/来源证据见 [T005](../../../test/T005-csapp-part-two.md)。

仓库根目录运行 `python3 tools/project.py check --book csapp`。完整检查包含来源与逐题页码、全部程序同步、严格编译、适用的 ASan/UBSan、跨语言输出和独立参考；`--quick` 只作静态检查。浮点全量与更大模型验证的条件和范围见逐章 review JSON。正文阅读与本地发布包的具体浏览器证据见 [T003](../../../test/T003-csapp-companion.md)。

第三部分独立边界回归由 `books/csapp/tools/part_three_regressions.py` 进入根检查：短读写/中断变体、二进制复制与继承 fd、地址转换、HTTP 分片/HEAD/长度/慢接收端截止时间、交错与死锁参考、三种 tfgets 真实部分行超时。设计与证据见 [T007](../../../test/T007-csapp-part-three.md)。

第三部分评估修复的真实 Expect 握手、跨接入窗口 HTTP/echo 与 SIGTERM 继承环境回归随根检查执行，设计与证据见 [T008](../../../test/T008-csapp-part-three-review-fixes.md)。

第二轮评估回归见 [T010](../../../test/T010-csapp-review-v2-fixes.md)：首部 OWS 与 Host/Expect 组合、断言开关与错误变体、实际 C/Python CGI 的重叠请求、通知合并及描述符/信号恢复随根检查执行。CGI exec 失败返回 502；可信子程序设五秒 alarm，超时可能导致响应截断，协议驱动明确验证此失败边界及后续服务恢复。

`ch03_procprob_alias.c` 在小端 LP64、8位有符号 char 下比较3.33两种内存更新顺序：合法别名时为1与257，独立对象时一致。它执行C内存顺序模型，不宣称运行了题给x86汇编。`ch09_space.c` 是Darwin专用空间实验，需与 `ch09_allocator.c` 同目录，使用 `MallocMaxMagazines=1` 固定本次私有scalable zone设置；编译时不启用ASan以保持实际libc后端。它对64/512块相同轨迹按每次操作采样，用峰值请求字节除以最大块存储后备页字节，逐次核对区域页并集与zone统计。双方区域外控制状态不计；该指标不代表默认nano/xzone分派或物理RSS。`tools/content_review_regressions.py` 独立核对载荷、操作数和除法，并以错误重排和活块分母变体验证检查能力。
