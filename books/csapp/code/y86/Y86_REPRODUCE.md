# Y86-64：第 4 章 HCL 变体的复现实验

本说明对应 CS:APP 第三版 Global Edition 的 4.52–4.58。实验以作者 [Architecture Lab](https://csapp.cs.cmu.edu/3e/labs.html) 的 [archlab-handout.tar](https://csapp.cs.cmu.edu/3e/archlab-handout.tar) 为基础，补丁只包含七个 HCL 模板的控制方程改动。`build_y86_variants.sh` 构建文字界面的模拟器，七个可执行文件分别命名为 `ex4-52` 至 `ex4-58`。

本次执行平台是 macOS 15.8.1 / arm64，使用 Apple Clang。原始 yas、yis、ssim、psim 和七个变体均成功编译。GNU89、`-fcommon` 与 macOS 的 `-ll` 用于兼容该发行包的旧 C 和 Lex 构建方式；GUI 关闭。编译器对原始 C 的旧式函数声明等给出了警告，完整日志保存在实验记录中。

## 来源、补丁和构建

下载包的 SHA-256 为：

```
archlab-handout.tar
586fc3347214ccd90e1c7cbfa74560c59584f8cf452d81c653acfd73344797d4

内部 sim.tar
aac789d967ccd4db530a177c827401feecd905ac9119929abe4200575735ce28
```

把本说明、`csapp-ex4-52-58.patch` 和 `build_y86_variants.sh` 放在同一目录，并在该目录执行。命令在 `y86-run` 下展开源码和保存编译产物：

```sh
support_dir=$(pwd)
work_dir="$support_dir/y86-run"
mkdir -p "$work_dir"
curl --fail --location https://csapp.cs.cmu.edu/3e/archlab-handout.tar \
  -o "$work_dir/archlab-handout.tar"
shasum -a 256 "$work_dir/archlab-handout.tar"
tar -xf "$work_dir/archlab-handout.tar" -C "$work_dir"
shasum -a 256 "$work_dir/archlab-handout/sim.tar"
tar -xf "$work_dir/archlab-handout/sim.tar" -C "$work_dir"
sim_tree="$work_dir/sim"
make -C "$sim_tree/misc" CC=clang LEXLIB=-ll \
  'LCFLAGS=-O1 -std=gnu89' 'CFLAGS=-Wall -O2 -fcommon -std=gnu89' all
make -C "$sim_tree/seq" CC=clang GUIMODE= TKLIBS= TKINC= \
  'CFLAGS=-Wall -O2 -fcommon -std=gnu89' ssim
make -C "$sim_tree/pipe" CC=clang GUIMODE= TKLIBS= TKINC= \
  'CFLAGS=-Wall -O2 -fcommon -std=gnu89' psim
patch --dry-run -d "$sim_tree" -p1 < "$support_dir/csapp-ex4-52-58.patch"
patch -d "$sim_tree" -p1 < "$support_dir/csapp-ex4-52-58.patch"
sh "$support_dir/build_y86_variants.sh" "$sim_tree" "$work_dir/bin"
```

补丁和模板对应如下：

| 习题 | 发行包模板 | 实验内容 |
| --- | --- | --- |
| 4.52 | `seq/seq-full.hcl` | SEQ 的 iaddq |
| 4.53 | `pipe/pipe-nobypass.hcl` | 无转发的完整停顿控制 |
| 4.54 | `pipe/pipe-full.hcl` | PIPE 的 iaddq |
| 4.55 | `pipe/pipe-nt.hcl` | 条件跳转预测不跳 |
| 4.56 | `pipe/pipe-btfnt.hcl` | 后向跳、前向不跳 |
| 4.57 | `pipe/pipe-lf.hcl` | load 到 store 数据的迟转发 |
| 4.58 | `pipe/pipe-1w.hcl` | 单写端口的两步 popq |

题书与下载包存在三个接口差异。题书把 4.53 模板称为 `pipe-stall.hcl`，下载包称为 `pipe-nobypass.hcl`。4.55、4.56 的题书使用 `J_YES`，下载包给出的 HCL 名称是 `UNCOND`，并绑定 C 常量 `C_YES`；补丁显式加入 `wordsig J_YES 'C_YES'`，保持无条件跳转功能号为 0。4.58 题书把内部 `IPOP2` 编号写为 `0xE`，下载包的 `I_POP2` 枚举值是 `0xD`；补丁保留下载包的 `wordsig IPOP2 'I_POP2'`。这个编号只在取指时内部产生，程序中的 popq 机器码仍是 `0xB0`。

补丁已在重新解开的官方包中通过预检查和实际应用；七份应用后的 HCL 与实际受测 HCL 逐字节相同，随后重新编译并各运行了代表程序。

## 指令、冒险和程序验证

`sim/ptest` 的四组基本回归分别检查单条指令、条件跳转、控制交集和数据冒险；`etest.pl` 另外检查异常之后的条件码和内存写入隔离。下面以 4.54 为例，`-i` 要求把 iaddq 加入测试：

```sh
(
  cd "$sim_tree/ptest"
  for test_script in optest jtest ctest htest etest; do
    perl -I. "$test_script.pl" -s "$work_dir/bin/ex4-54" -i
  done
)
```

4.52 也使用 `-i`；基础 SEQ/PIPE 和其余变体省略该参数。需要检查输出中的 `All ... ISA Checks Succeed`：这套旧回归脚本的进程退出码不足以单独代表所有 ISA 比较通过。

| 模型 | op | jump | control | hazard | exception | 合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 原始 SEQ | 49 | 64 | 22 | 600 | 12 | 747 |
| 原始 PIPE | 49 | 64 | 22 | 600 | 12 | 747 |
| 4.52 | 58 | 96 | 22 | 756 | 12 | 944 |
| 4.53 | 49 | 64 | 22 | 600 | 12 | 747 |
| 4.54 | 58 | 96 | 22 | 756 | 12 | 944 |
| 4.55 | 49 | 64 | 22 | 600 | 12 | 747 |
| 4.56 | 49 | 64 | 22 | 600 | 12 | 747 |
| 4.57 | 49 | 64 | 22 | 600 | 12 | 747 |
| 4.58 | 49 | 64 | 22 | 600 | 12 | 747 |

以上共 7,117 次比较均成功。它们证明这些受测程序的结束状态与同包的 ISA 解释器一致；控制方程的一般正确性仍需结合正文中的依赖分析和条件组合推导。

`sim-cases/` 提供从正文程序组成的驱动及独立边界用例。把相应 `.ys` 交给 yas 后，分别运行解释器和控制器：

```sh
"$sim_tree/misc/yas" "$support_dir/sim-cases/page-4-47-mixed.ys"
"$sim_tree/misc/yis" "$support_dir/sim-cases/page-4-47-mixed.yo"
"$sim_tree/seq/ssim" -t -v 1 "$support_dir/sim-cases/page-4-47-mixed.yo"
"$sim_tree/pipe/psim" -t -v 1 "$support_dir/sim-cases/page-4-47-mixed.yo"
"$work_dir/bin/ex4-53" -t -v 2 "$support_dir/sim-cases/noforward-h-b-r.yo"
```

最后一条也需先用 yas 汇编同名 `.ys`；`-v 2` 展开逐周期状态。无转发交集用例在 cycle 4 同时出现 D 中的 ret、E 中实际不跳的 jne、M 中将写 `%rsp` 的 irmovq，下一周期 D/E 成为气泡，取指恢复到正确的顺序地址。

正文 4.4、4.5、4.6 的代表输入以及 4.47–4.49 各三种排序输入，共 24 次 SEQ/PIPE ISA 比较成功。额外可比用例包括 iaddq 的负数、溢出、load 依赖、紧随条件分支、老异常屏蔽；无转发的 H∩B 与 H∩B∩R；条件目标等于顺序地址、无条件目标只执行一次、循环与 ret；load→store 数据和地址依赖；连续 pop、老 load 导致的重取停顿、popq %rsp→ret、CC 保持和错误路径取消，共 29 次比较成功。

4.57 的时间差也与机制一致：`lf-load-push-data` 从基础 PIPE 的 7 cycles 降至 6；`lf-load-store-address` 和 `lf-load-rsp-push` 均保持 6，地址依赖的停顿保留。

## 周期口径与异常状态约定

正文对标准 PIPE 有限程序使用的

```
T_total = N + 4 + L + 2B + 3R
```

计入开始的四拍填充。官方 `psim.c` 的 performance monitoring 在首条非气泡指令进入 W 时才开始累计 `cycles`，因而 `CPI:` 一行中的周期数省略这四拍。对于本说明的标准 PIPE 排序实验，有 `T_total = psim_cycles + 4`。例如，4.47 已排序数组的 `N=175`，psim 输出 192 cycles，含填充总周期为 196；混合数组的 `N=189`，psim 输出 220 cycles，含填充为 224。正文九行排序性能表均与这个关系吻合。公式中的 L、B、R 是标准 PIPE 的罚时事件；改变预测、转发或加入内部 pop 步骤后，应依据变体实际控制重新计算。

4.58 的内部 IPOP2 消耗周期，但官方计数器把它排除在指令数之外。这样 CPI 的分母仍按原程序的 popq 计一次。输出靠前的 `instructions executed` 来自模拟步数接口，与最后 `CPI:` 行的退休指令计数需要分别读取。

原始官方包对非法 push/pop 存在一项 ISA 与硬件模型的状态差异：`misc/isa.c` 的 push 分支在检查写内存成功前更新 `%rsp`，pop 分支在检查读成功前更新 `%rsp`；原始 SEQ/PIPE 在 ADR 处停止，呈现旧 `%rsp`。因此原包自带 `prog10.ys` 在原始 SEQ、PIPE 上均输出 `ISA Check Fails`，而状态均为 ADR、后续指令未提交。用 `pop-invalid-address.ys` 可单独复现：输入 `%rsp=0x100000`，yis 停止时为 `0x100008`，SEQ、PIPE 与 4.58 均为 `0x100000`。

4.58 正文采用“失败访问不提交寄存器更新”的 ISA 约定。第一步预读原栈槽检查地址，异常时不写回，第二步由标准异常控制取消。因此该非法 pop 的 `%rsp` 保持符合正文约定；与官方 yis 的这一次比较失败应随原始日志保留。正常地址的 pop、popq %rsp 和 load/use 回归均通过。

执行范围包括列出的控制器、结束状态比较、特定逐周期轨迹和周期对照。跨地址符号位的方向比较由独立有符号数学模型检查，官方文字模拟器分配的低地址内存无法容纳那类跳转目标；畸形编码和全部可能程序也超出这组运行样本。
