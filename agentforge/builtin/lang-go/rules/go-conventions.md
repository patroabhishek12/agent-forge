---
id: go-conventions
description: Go coding conventions and project structure rules
apply_to: ["**/*.go"]
---

## Naming
- Exported identifiers: `PascalCase`. Unexported: `camelCase`.
- Interfaces: name by behaviour + `-er` suffix (`Reader`, `PaymentStorer`).
- Packages: short, lowercase, single word. No underscores or mixedCase.
- Error variables: `ErrNotFound`, `ErrInvalidInput` (sentinel errors via `errors.New`).

## Project layout (standard Go layout)
```
cmd/<service>/main.go   — entry point, wires dependencies
internal/
  domain/               — types, business rules, pure functions
  port/                 — interface definitions (no implementations)
  adapter/
    postgres/           — DB implementation
    http/               — HTTP handlers (chi / net/http / gin)
  config/               — config struct loaded from env via `envconfig` or `viper`
pkg/                    — reusable packages exposed to external callers
```

## Error handling
- Always check returned errors. Never `_` an error silently.
- Wrap errors with context: `fmt.Errorf("paymentService.Create: %w", err)`.
- Use `errors.Is` / `errors.As` for checking error types.
- Define sentinel errors at the domain level; translate to HTTP status in adapter layer.

## Code style
- Format with `gofmt` / `goimports` (enforced via `golangci-lint`).
- Max function length: 40 lines (prefer smaller). Extract helpers liberally.
- Avoid `init()` except for top-level registration (e.g. `sql.Register`).
- Use context (`context.Context`) as the first parameter in all I/O functions.

## Testing
- Files: `<file>_test.go` alongside source.
- Use `testify/assert` and `testify/require` for assertions.
- Table-driven tests for multiple input cases.
- Mock interfaces using `mockery`-generated mocks or `gomock`.
- Run `go test ./... -race` in CI.
