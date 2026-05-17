---
id: tests
description: Testing conventions for Kotlin Spring Boot
apply_to: ["**/*Test.kt", "**/test/**/*.kt"]
---
- Use JUnit 5 with Kotest assertions.
- Each test class names what it tests: `OrderServiceTest`, not `Tests`.
- Mock external services with MockK; never use Mockito.
- Integration tests live under `src/test/integration` and use Testcontainers.
