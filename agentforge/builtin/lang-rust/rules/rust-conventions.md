---
id: rust-conventions
description: Rust coding conventions and project structure rules
apply_to: ["**/*.rs"]
---

## Naming
- Types and traits: `PascalCase`. Functions, methods, variables, modules: `snake_case`.
- Constants and statics: `UPPER_SNAKE_CASE`. Lifetimes: short lowercase (`'a`, `'conn`).

## Module structure (workspace or single crate)
```
src/
  main.rs / lib.rs    — crate root, minimal glue
  domain/             — pure business logic, no I/O, no async
  ports/              — traits defining outbound interfaces (repository, messaging)
  adapters/           — implementations of ports (DB, HTTP client, MQ)
  api/                — HTTP handlers (axum / actix-web routers)
  config.rs           — configuration struct, loaded from env
  error.rs            — unified Error enum with thiserror
```

## Error handling
- Define a crate-level `Error` enum using `thiserror`.
- Never use `.unwrap()` in library code. Use `?` propagation.
- `.expect()` is acceptable only in `main` during startup for non-recoverable
  configuration failures.

## Async
- Use `tokio` as the async runtime. Annotate `main` with `#[tokio::main]`.
- Avoid `async` in the domain layer — keep it synchronous for testability.
- Use `Arc<T>` for shared state passed into handlers.

## Code style
- Format with `rustfmt` (run `cargo fmt` before every commit).
- Lint with `cargo clippy -- -D warnings`.
- Max line length: 100 characters (set in `rustfmt.toml`).
- Prefer `impl Trait` in function arguments over generics where clarity is equal.

## Testing
- Unit tests: `#[cfg(test)] mod tests` in the same file.
- Integration tests: `tests/` directory at crate root.
- Use `cargo nextest` for faster parallel test runs.
- Mock trait implementations using `mockall` for port traits.
