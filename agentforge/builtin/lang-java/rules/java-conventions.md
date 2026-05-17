---
id: java-conventions
description: Java coding conventions and layering rules
apply_to: ["**/*.java"]
---

## Naming
- Classes: `PascalCase`. Interfaces: prefix with `I` only when it aids clarity (prefer no prefix).
- Methods and variables: `camelCase`. Constants: `UPPER_SNAKE_CASE`.
- Packages: lowercase, reverse-domain (`com.acme.payments.service`).

## Layering (Spring / Quarkus projects)
```
controller/   → @RestController / @Path  — HTTP boundary only, no business logic
service/      → @Service / @ApplicationScoped  — business logic, orchestration
repository/   → @Repository / @ApplicationScoped  — data access via JPA/JDBC
model/        → @Entity, POJOs, record classes
dto/          → request/response DTOs (never expose @Entity directly)
exception/    → custom exceptions extending RuntimeException
config/       → @Configuration / @ApplicationScoped beans
```
- Services must not import repository classes from other bounded contexts — use events or APIs.
- Controllers must not contain @Transactional.
- Repositories must not contain business logic.

## Code style
- Max line length: 120 characters.
- Use `var` for local variables when the type is obvious from the right-hand side.
- Prefer `Optional<T>` over returning `null` from service methods.
- Use records for immutable DTOs (Java 16+).
- Annotate all REST endpoints with `@Operation` (OpenAPI) for documentation.

## Testing
- Unit tests: JUnit 5 + Mockito. File alongside source: `src/test/java/...`.
- Test class naming: `<ClassName>Test`.
- Integration tests: use `@SpringBootTest` / `@QuarkusTest`; name `<ClassName>IT`.
- Coverage target: 80 % line coverage on service layer.

## Error handling
- Use a global `@ControllerAdvice` / `@Provider ExceptionMapper` to translate
  exceptions to problem-detail JSON (`application/problem+json`).
- Never swallow exceptions with empty catch blocks.
- Log at WARN for expected business errors; ERROR for unexpected failures.
