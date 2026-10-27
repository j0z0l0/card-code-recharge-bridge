# Contributing

Thanks for improving the Skill.

## Before opening an Issue

- Remove all API keys, passwords, card codes, order exports and customer data.
- Provide the smallest reproducible example.
- State whether the problem is in the Skill instructions, a helper script, or a third-party platform.
- Do not publish private platform endpoints or reverse-engineered signatures unless you have confirmed that disclosure is lawful and permitted by the platform's terms.

## Development workflow

1. Keep the Skill focused on connecting an existing application product to an existing card-code platform product.
2. Do not add business-model design, pricing advice, inventory management or unrelated account-system features.
3. Preserve the payment-safety rules in `SKILL.md`, especially idempotency and test-data retention.
4. Update the relevant reference, template or adapter when changing behavior.
5. Run the local validation:

```bash
python scripts/validate_skill.py .
```

6. Do not commit generated archives, `.env` files, credentials, logs, database dumps or real order/card data.

## Pull requests

Describe:

- what changed;
- why the change is needed;
- which tools or adapters are affected;
- what was tested;
- whether any real payment was involved. Real-payment tests must not be added to repository fixtures.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
