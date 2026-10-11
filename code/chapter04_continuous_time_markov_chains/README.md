# 第 4 章程序

从项目根目录执行以下命令；先用 `make -C code` 编译 C 程序。

## 跳转频率与真实时间占比

两状态跳转速率分别为 2、1，记录十万次跳转，即五万个完整往返。输出状态、跳转频率、按真实时间加权的占比；理论时间比例为 1/3、2/3。

Python：

```sh
python3 code/chapter04_continuous_time_markov_chains/ctmc.py
```

C：

```sh
./code/build/ctmc
```

[回到正文](../../notes/chapter04_continuous_time_markov_chains.html#pair-ctmc) · [C 源文件](ctmc.c) · [Python 源文件](ctmc.py)
