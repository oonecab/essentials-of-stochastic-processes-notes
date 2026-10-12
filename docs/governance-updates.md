# 更新项目治理

`.project-governance.json` 保存项目类型、治理级别、Agent 开关、技术边界与命令。配置改变后通过 `init-project-governance` 技能生成文件；受管区块由生成器维护，区块外保留项目说明。规则、实际部署步骤与书籍正文各有独立权威文档，不复制进代理文件。

在主仓库根目录运行以下流程，其中 `<skill-directory>` 是已安装或由任务明确指定的技能目录：

```sh
# 读取当前 .project-governance.json，预览全部计划
python3 <skill-directory>/scripts/init_project.py --target .

# 审阅 CREATE/UPDATE/UNCHANGED/PRESERVE/CONFLICT 后，再应用
python3 <skill-directory>/scripts/init_project.py --target . --apply

# 检查受管区块、源码目录、配置与兼容入口
python3 <skill-directory>/scripts/validate_project.py .
```

预览出现 CONFLICT 时先审阅双方内容，不自动覆盖。README 和 `.gitignore` 保留为人工维护文件，生成器会提示 PRESERVE；本项目使用普通校验确认受管内容，另由 `tools/check_structure.py` 检查登记目录、命令、适配器和真实文档链接。严格模式将这两项人工文件提示也视为失败，其结果不能误报为受管 drift。

同配置重新预览应为 UNCHANGED 与两项 PRESERVE。技能升级后，如生成器版本不一致，使用新生成器重新预览、审阅并应用，不只手改版本字段。技术栈或兼容边界改变时同步 [TECH.md](../TECH.md) 的项目自主管理说明及追加索引，必要时新增 ADR。具体影响联动遵循 [变更控制](governance/CHANGE_CONTROL.md)。

该技能生成治理骨架，不执行已登记的项目命令；生成器校验通过之后仍需执行对应的程序、构建、浏览器或部署验证。当前验证入口及范围见 [根 README](../README.md)与 [测试设计](../test/T001-project-merge.md)。
