# 第 5 章程序

从项目根目录执行以下命令；先用 `make -C code` 编译 C 程序。

## 停止随机游走

从 0 出发，每步以相同概率加减 1，到首次绝对值达到 5 时停止。重复十万次，输出平均退出时间及从正边界退出的频率；理论值为 25、0.5。

Python：

```sh
python3 code/chapter05_martingales/stopping.py
```

C：

```sh
./code/build/stopping
```

[回到正文](../../notes/chapter05_martingales.html#pair-stopping) · [C 源文件](stopping.c) · [Python 源文件](stopping.py)
