# 第 3 章程序

从项目根目录执行以下命令；先用 `make -C code` 编译 C 程序。

## 更新周期的长度偏置

周期长度 1 和 9 各占一半，仿真十万个完整周期。输出周期长度、按周期计的频率、按时间计的占比；理论时间比例为 0.1 和 0.9。

Python：

```sh
python3 code/chapter03_renewal_processes/renewal.py
```

C：

```sh
./code/build/renewal
```

[回到正文](../../notes/chapter03_renewal_processes.html#pair-renewal) · [C 源文件](renewal.c) · [Python 源文件](renewal.py)
