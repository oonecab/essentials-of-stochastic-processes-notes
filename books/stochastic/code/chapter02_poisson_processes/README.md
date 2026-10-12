# 第 2 章程序

从项目根目录执行以下命令；先用 `make -C code` 编译 C 程序。

## 指数间隔与泊松计数

速率为每小时 3，观察两小时，进行十万次独立重复。输出 k、理论概率和仿真频率；最后一类汇总 16 次及以上。C/Python 使用相同伪随机数生成器和固定种子。

Python：

```sh
python3 code/chapter02_poisson_processes/poisson.py
```

C：

```sh
./code/build/poisson
```

[回到正文](../../notes/chapter02_poisson_processes.html#pair-poisson) · [C 源文件](poisson.c) · [Python 源文件](poisson.py)
