# 卡密平台无感充值打通

> 本 Skill 由 **Ai易道场** 在统一账户、计费与权益系统的实践中整理。  
> 官网：[www.aiydc.com](https://www.aiydc.com)

面向技术小白和试水商业化项目的跨工具 Skill。它只负责把用户已有应用商品与已有卡密平台商品接通，不设计商业模式、商品、价格或库存。

## 成品介绍

完整的产品背景、方案思路、风险和接入说明见：

- [`references/product-overview.md`](references/product-overview.md)

README 只提供快速说明；具体执行仍以 `SKILL.md` 和 `references/` 为准。

## 流程

```text
扫描应用工作区
→ 判断已有支付/兑换能力
→ 分类平台链接
→ 生成商品映射建议
→ 输出方案并自我审核
→ 用户授权
→ 实施、测试、部署
→ 交接
```

## 最小输入

- 应用项目目录（当前工作区明确时不需要询问）
- 卡密平台名称
- 具体商品页链接（优先）
- 可选：支付/收银台链接
- 修改、测试、部署授权

平台凭据通过本地环境配置，不通过聊天发送。

## 快速使用

```text
$card-code-recharge-bridge
```

然后提供应用目录和卡密平台商品链接。

## 环境要求

- Python 3.10+
- PowerShell 5.1+（仅 Windows 适配器安装脚本需要）
- 无第三方 Python 依赖

## 发布前校验

```bash
python scripts/validate_skill.py .
```

## 扫描工具

```bash
python scripts/inspect_app.py <应用目录>
python scripts/classify_platform_link.py "<平台链接>"
```

## 安装到本机工具

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_adapters.ps1 -WhatIf
powershell -ExecutionPolicy Bypass -File scripts/install_adapters.ps1
```

可选安装豆包提示词包：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_adapters.ps1 -Targets doubao
```

## 实测安全规则

- 真实付款测试必须先取得用户明确同意；
- 对账完成前不清理订单、支付事件、卡密和权益记录；
- Skill 只负责打通支付结果与已有权益，不默认扩展到余额、会员或返赠体系。

## 开源许可

本项目采用 [MIT License](LICENSE)。可以免费使用、修改、分发和商用，但必须保留版权与许可证声明。

安全问题和贡献方式见 [SECURITY.md](SECURITY.md) 与 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 推广与隶属关系声明

README 中的 Ai易道场官网和邀请码属于项目作者的推广链接。项目与 Codex、Claude Code、Hermes、Trae、Zcode、豆包及其他第三方工具或卡密平台不存在隶属、授权或背书关系。

## 风险边界

- 第三方卡密平台可能改版、限流或停止发卡；
- 适合验证付费和试运行；
- 收入稳定后应迁移到官方支付；
- 技术兜底不能替代用户承担支付与经营合规责任。

