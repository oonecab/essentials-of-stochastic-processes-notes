# 第 6 章程序

从项目根目录执行以下命令；先用 `make -C code` 编译 C 程序。

## 完整二叉期权树

输入九项：N、S0、u、d、r、K、kind、american、barrier。N 在 0 到 12 之间，须满足 0<d<1+r<u。kind=0/1/2/3/4/5/6/7 分别是看涨、看跌、亚洲均价看涨、浮动执行价回望看跌、浮动执行价回望看涨、数字看涨、上限为60的看涨、上障碍敲出的看跌。american=0/1 表示欧式/美式。输出完整历史路径、股价、价值、持股数和动作；动作 0/1/2 表示继续/行权/到期。路径相关支付保留全部历史。

Python：

```sh
python3 code/chapter06_mathematical_finance/finance.py <<'EOF'
1 110 1.1 0.9 0.04 113 0 0 0
EOF
```

C：

```sh
./code/build/finance <<'EOF'
1 110 1.1 0.9 0.04 113 0 0 0
EOF
```

[回到正文](../../notes/chapter06_mathematical_finance.html#pair-finance) · [C 源文件](finance.c) · [Python 源文件](finance.py)

## Black–Scholes 与 CRR 收敛

输入五项：现价 S、执行价 K、期限 T、连续复利利率 r、波动率 sigma。输出看涨价、看跌价和看涨 Delta。convergence 模式进一步给出 16、32、64、128、256、512 个期数的 CRR 看涨价；该模式要求正期限和正波动率，并逐个检查二叉无套利条件。

Python：

```sh
python3 code/chapter06_mathematical_finance/bs.py convergence <<'EOF'
100 100 1 0.05 0.2
EOF
```

C：

```sh
./code/build/bs convergence <<'EOF'
100 100 1 0.05 0.2
EOF
```

[回到正文](../../notes/chapter06_mathematical_finance.html#pair-bs) · [C 源文件](bs.c) · [Python 源文件](bs.py)

美式期权的理论规则为：正的即时支付大于或等于继续价值时最早行权。浮点实现设置 `32*epsilon*max(abs(iv),abs(cv))` 的相对舍入容差，以免确切等值节点因末位误差误标继续；不加固定的绝对价值下限，极小正价格仍按其自身尺度比较。零支付的等值节点继续持有。树的数值和动作均与独立有理数路径枚举核对，包括十二期完整树、九期亚洲均价及极小价格。

C 和 Python 对亚洲均价都按历史顺序先除项数再累加，避免 Python 新版本补偿求和改变舍入路径。输入字段最多127字符；错误格式与参数返回2，溢出、下溢为零或非有限结果返回3，明确捕获的资源失败返回4，标准错误包含说明。
