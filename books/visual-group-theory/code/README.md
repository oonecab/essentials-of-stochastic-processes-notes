# 从群动作到 Galois 理论的程序

十组程序使用 Python 3 标准库或 C11，无第三方运行依赖。下载任一语言源码即可运行；字词按时间从左到右执行。

## 第 1 章：三幅画的动作枚举

[Python](actions.py) · [C11](actions.c)。

在[第 1 章的图与推演](../notes/chapter01_what_is_a_group.html#three-pictures)理解 a、b 后运行本例。三幅画 A、B、C 各不相同；位置从左到右固定。a 交换左/中，b 交换中/右，字词从左到右执行。e 只是输出中空操作的名字，命令行输入使用空串表示它。

下载 `actions.py` 后运行 `python3 actions.py`。下载 `actions.c` 后运行：

```sh
clang -std=c11 -Wall -Wextra -Werror -pedantic actions.c -o actions
./actions
./actions ab
./actions ba
./actions ''
```

默认输出依次为 `e ABC`、`a BAC`、`b ACB`、`ab BCA`、`ba CAB`、`aba CBA`。有一个参数时只输出从 ABC 出发的最终排列：`ab` 得 BCA，`ba` 得 CAB；空串得 ABC。Python 使用相同参数。包含其他字符或多个参数时，两个命令都报告错误、退出码 2 且无标准输出。

两版都按广度优先发现新排列，已有排列不重复入队，按 a 后 b 的顺序扩展。三幅不同画的状态最多 3!=6 个；到达一个完整标记排列唯一决定位置重排，因此这里可以借状态枚举动作。一般群作用不能直接用“状态数”代替“群的阶”。

C 使用固定 6 项数组和带终止符的 7 字节路径槽，容量写入前检查；所有位置值限于 0、1、2，无动态分配与数值近似。Python 使用整数元组和列表，失败输入先校验。固定实例最多扩展 12 条生成元边；若同样的线性查重方法用于 V 个长度 n 的状态、k 个生成元，时间上界 O(k V² n)，另有路径存储成本。命令行单条长字词逐字符执行，时间与长度成正比，状态存储为常数。

## 第 2 章：正多边形地图

[推导与代码](../notes/chapter02_what_do_groups_look_like.html#program-cayley) · [Python](cayley.py) · [C11](cayley.c)。

```sh
python3 cayley.py 5
clang -std=c11 -Wall -Wextra -Werror -pedantic cayley.c -o cayley
./cayley 5
```

默认 n=4，接受 n=3…12。输出 2n 个动作、最短字词、坐标变换 sign/shift 及追加 r/f 后的目标编号。Python 字典查重，C 固定 24 项线性查重；一般证明在 2.19。非法参数退出 2，C 内部容量异常退出 3。

## 第 3 章：无限饰带

[推导与代码](../notes/chapter03_why_study_groups.html#program-frieze) · [Python](frieze.py) · [C11](frieze.c)。

```sh
python3 frieze.py hgh
clang -std=c11 -Wall -Wextra -Werror -pedantic frieze.c -o frieze
./frieze hghg
```

h 为左右反射，g 为右移一格再上下反射，G 是 g 的逆。输出 sx,sy,dx 表示 (x,y)→(sx*x+dx,sy*y)。hgh 得 (1,−1,−1)，hghg 得 (1,1,0)。最多 10000 字符，非法输入退出 2；空串为恒等，输出 e 不作为输入字母。有限字词核查不等于枚举无限群。

## 第 4 章：有限表的完整公理检查

[推导与代码](../notes/chapter04_algebra_at_last.html#program-tables) · [Python](tables.py) · [C11](tables.c)。

```sh
python3 tables.py
clang -std=c11 -Wall -Wextra -Werror -pedantic tables.c -o tables
./tables
python3 tables.py --stdin < table.txt
./tables --stdin < table.txt
```

无参数检查 V₄。table.txt 第一项 n（1…16），随后按行写恰好 n² 项，元素编号 0…n−1。每个 ASCII 整数最多四位，可带负号。下面是原题 4.10，返回 1 并给出不结合的三元组：

```text
3
0 1 2
1 0 0
2 0 0
```

全部公理成立返回 0；合法表数据不成群返回 1；缺项、多项、非法字元或 n 越界返回 2。先检查封闭性再作下标访问，结合律检查全部 n³ 个三元组，恒等与逆要求双侧。默认输出 CLOSURE OK、ASSOCIATIVE OK、IDENTITY 0、INVERSES OK、GROUP YES。

## 第 5—8 章：结构与映射

| 章节 / 源码 | 参数 | 默认实例与输出 |
|---|---|---|
| 5：[permutations.py](permutations.py) / [C11](permutations.c) | 两个 1…8 次一行置换，逗号分隔 | 比较 p 后 q 与 q 后 p，列循环、阶、符号、逆 |
| 6：[subgroups.py](subgroups.py) / [C11](subgroups.c) | n=1…6，默认 4 | D₄ 全部 10 个子群、阶、指数和左右陪集 |
| 7：[products.py](products.py) / [C11](products.c) | n,m,u；2≤n≤12，1≤m≤6，nm≤24，u 为单位且 uᵐ=1 mod n | 默认 D₄；输出元素阶、完整表与旋转子群的商 |
| 8：[homomorphisms.py](homomorphisms.py) / [C11](homomorphisms.c) | m,n=1…12；每项至多两位 ASCII 数字 | 默认 C₁₂→C₈ 的 4 个同态，全部核、像及纤维 |

下载后在源码所在目录运行，例如：

```sh
python3 permutations.py 2,3,4,1 2,1,3,4
python3 subgroups.py 4
python3 products.py 4 2 3
python3 homomorphisms.py 12 8
clang -std=c11 -Wall -Wextra -Werror -pedantic homomorphisms.c -o homomorphisms
./homomorphisms 12 8
```

其他 C 文件用同一编译选项替换文件名即可。四组合法调用返回 0，非法参数返回 2、标准错误解释原因且标准输出为空。数字表示和有限容量都在各章程序段解释；这些限制控制枚举成本，不限制数学定理的适用范围。

## 第 9—10 章：Sylow 与域自同构

[Sylow 推导](../notes/chapter09_sylow_theory.html#program-sylow)及 [sylow.py](sylow.py) / [C11](sylow.c) 接受 n=2…5 和不大于 n 的素数 p（每项一位 ASCII 数字），默认 S₄ 的 p=2。枚举所有置换、Sylow 子群的完整元素编号、正规化子阶与自然作用的轨道稳定子。它构造一个最大 p 子群后取全部共轭，正确性依赖正文证明；独立检查另从单位子群逐次添元枚举所有子群。

[Galois 推导](../notes/chapter10_galois_theory.html#program-galois)及 [galois.py](galois.py) / [C11](galois.c) 接受六个 −100…100 的整数 a,b,c,d,e,f，表示 a+bt+ct²+ds+ets+ft²s，t³=2、s²=−3。默认六项全为 1。输出六个自同构、根置换、迹以及与共轭的乘积；Fraction / 约分有理数保证精确计算。C 的 int64_t 安全范围限于这个固定算法与输入界限；扩大范围需要另审中间乘加。

```sh
python3 sylow.py 5 3
clang -std=c11 -Wall -Wextra -Werror -pedantic sylow.c -o sylow
./sylow 4 2
python3 galois.py 1 1 1 1 1 1
clang -std=c11 -Wall -Wextra -Werror -pedantic galois.c -o galois
./galois 1 1 1 1 1 1
```

两组合法调用返回 0；非法参数返回 2、无标准输出。Sylow 默认给 3 个 8 阶子群，各正规化子阶 8；Galois 默认迹为 [6,0,0,0,0,0]，z 与其共轭的乘积为 [20,16,12,0,0,0]。

## 校验

维护源在本目录，HTML 中的阅读副本由 `tools/sync_code.py --write` 同步。根目录 `python3 tools/project.py check --book visual-group-theory` 实际编译运行、检查 C/Python 输出、全部有限状态复合、边界及非法输入。C 以 ASan/UBSan 再执行；一般的群性质仍依赖正文证明。
