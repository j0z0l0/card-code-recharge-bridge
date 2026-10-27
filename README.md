# Card-Code Recharge Bridge

[English](README.md) | [简体中文](README.zh-CN.md)

> An open-source cross-tool AI Skill maintained by **Ai易道场**.  
> Website: [www.aiydc.com](https://www.aiydc.com)

This Skill connects products and card-code items that the user already owns. It focuses only on the bridge between payment and fulfillment:

```text
Existing app product
→ card-code platform checkout
→ payment
→ server-side payment query
→ card-code retrieval
→ existing redemption / entitlement flow
→ seamless fulfillment
```

It does not design pricing, product tiers, inventory or business models.

## Full guide

A detailed implementation reference is available in Chinese:

- [`references/product-overview.md`](references/product-overview.md)

The executable instructions are in `SKILL.md` and the relevant files under `references/`.

## Supported workflow

```text
Inspect the application workspace
→ detect existing payment and redemption capabilities
→ classify the card-platform link
→ propose a product mapping
→ produce a plan and self-review it
→ obtain user authorization
→ implement and test
→ deploy only when approved
→ hand off
```

## Minimum input

- Application project directory, unless the current workspace is already clear
- Card-code platform name
- Specific product-page URL, preferred
- Optional checkout/payment URL
- Authorization before code changes, tests or deployment

Platform credentials must be configured locally and must never be sent through chat.

## Quick use

```text
$card-code-recharge-bridge
```

Then provide the application directory and card-platform product URL.

## Requirements

- Python 3.10+
- PowerShell 5.1+ only for the Windows adapter installer
- No third-party Python dependencies

## Validate before release

```bash
python scripts/validate_skill.py .
```

## Inspection tools

```bash
python scripts/inspect_app.py <application-directory>
python scripts/classify_platform_link.py "<platform-link>"
```

## Install adapters

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_adapters.ps1 -WhatIf
powershell -ExecutionPolicy Bypass -File scripts/install_adapters.ps1
```

Optional Doubao prompt pack:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_adapters.ps1 -Targets doubao
```

## Real-payment safety rules

- Explicit user consent is required before a real-payment test.
- Do not delete orders, payment events, card codes, guest identities or entitlement records before reconciliation is complete.
- The Skill connects payment results to existing entitlements only. It does not expand into balance, membership, referral or bonus systems by default.

## Security and contributions

See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is released under the [MIT License](LICENSE). You may use, modify, distribute and commercialize it, provided that the copyright and license notices are retained.

## Promotion and affiliation

The Ai易道场 website and referral code in this repository are project-author promotional links. This project is not affiliated with, authorized by, or endorsed by Codex, Claude Code, Hermes, Trae, Zcode, Doubao, or any third-party card-code platform.

## Risk notice

- Third-party card-code platforms may change APIs, impose limits, suspend stores or stop issuing cards.
- This approach is suitable for payment validation and early operation, not as a permanent primary payment channel.
- A stable business should migrate to an official payment channel.
- Technical safeguards do not replace the operator's payment, tax and regulatory responsibilities.
