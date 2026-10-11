# 随机过程笔记的可运行示例

这里保存网页中七组 C11/Python 示例的源文件。六个目录按章节排列，第六章有完整期权树和 Black–Scholes/CRR 两组程序。Python 仅使用标准库；C 使用标准库和数学库。

| 章节目录 | 程序 | 用途 |
|---|---|---|
| [chapter01_markov_chains](chapter01_markov_chains/README.md) | linear.c / linear.py | P/Q 平稳分布、多步分布、退出概率及退出时间 |
| [chapter02_poisson_processes](chapter02_poisson_processes/README.md) | poisson.c / poisson.py | 指数间隔构造泊松计数 |
| [chapter03_renewal_processes](chapter03_renewal_processes/README.md) | renewal.c / renewal.py | 周期频率与时间频率的长度偏置 |
| [chapter04_continuous_time_markov_chains](chapter04_continuous_time_markov_chains/README.md) | ctmc.c / ctmc.py | 跳转频率与真实时间占比 |
| [chapter05_martingales](chapter05_martingales/README.md) | stopping.c / stopping.py | 随机游走首次退出及停时期望 |
| [chapter06_mathematical_finance](chapter06_mathematical_finance/README.md) | finance.c / finance.py；bs.c / bs.py | 完整路径期权树、Black–Scholes 与 CRR 收敛 |

在项目根目录编译全部 C 程序：

```sh
make -C code
```

可执行文件放在 `code/build/`。例如运行泊松计数：

```sh
./code/build/poisson
python3 code/chapter02_poisson_processes/poisson.py
```

输入、输出、参数与例子见各章说明。四个仿真程序固定种子，均无需输入。线性方程和两组金融程序从标准输入读取数据；输入模式、字段数、无套利条件或数值格式错误返回退出码2；奇异、病态、溢出等数值失败返回退出码3；明确捕获的资源分配失败返回退出码4。C／Python 均在标准错误输出原因。单个输入字段最多127字符，超长字段整体拒绝。

## 修改与验证

以后修改这里的 `.c`／`.py` 文件，然后同步网页：

```sh
python3 tools/sync_code.py --write
python3 tools/check_notes.py
```

`python3 tools/sync_code.py` 只检查一致性。程序登记和对应页面见 [programs.json](programs.json)。网页内保留完整代码阅读副本，以便离线阅读；每组代码旁有源文件下载入口。结构校验先逐字核对源文件与网页副本，再执行严格 C11、Python、数值基准和 ASan/UBSan 检查。

编译统一加入 `-ffp-contract=off`，避免 C 将乘加收缩成 FMA 后与 Python 的运算顺序不同。亚洲均价和线性求解的累加采用相同顺序，Black–Scholes 的零结果统一为正零。当前验证环境逐字核对两种语言的输出；其他编译器、数学库或平台应重新执行检查，不能仅凭源码一致保证末位数字相同。`make -C code clean` 清理七个可执行文件。

四个仿真使用 xorshift32（移位13／17／5），显示种子20261010。完整验证还在独立临时副本中替换为1、42、4294967295，核对语言一致性、理论均值、频率及时间占比，源文件的显示种子保持一致。
