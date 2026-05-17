---
name: java-codegen
description: >
  Triggered when a user asks to "scaffold a Java service", "generate a Spring controller",
  "create a Quarkus endpoint", "add a repository for <entity>", or requests new Java
  code from a story description with a Java project detected.
---

## Procedure

1. **Identify framework** — Spring Boot or Quarkus (check `pom.xml` / `build.gradle` deps).

2. **Determine what to generate** from the story or user description:
   - Entity / Record
   - Repository (Spring Data / Panache)
   - Service class
   - REST Controller / Resource
   - DTO classes (request + response)
   - Unit test stub

3. **Generate each layer in order** (bottom-up: entity → repository → service → controller):

   Entity example (Spring + JPA):
   ```java
   @Entity
   @Table(name = "payments")
   public class Payment {
       @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
       private Long id;
       // fields with validation annotations
   }
   ```

   Repository example:
   ```java
   @Repository
   public interface PaymentRepository extends JpaRepository<Payment, Long> {
       List<Payment> findByStatus(PaymentStatus status);
   }
   ```

   Service example:
   ```java
   @Service
   @RequiredArgsConstructor
   public class PaymentService {
       private final PaymentRepository repo;
       // business methods — no HTTP types
   }
   ```

   Controller example:
   ```java
   @RestController
   @RequestMapping("/api/v1/payments")
   @RequiredArgsConstructor
   @Tag(name = "Payments")
   public class PaymentController {
       private final PaymentService service;
       // @GetMapping, @PostMapping methods only — delegate to service
   }
   ```

4. **Place files** in the correct package directory following the project's existing structure.

5. **Generate test stub** alongside service:
   ```java
   @ExtendWith(MockitoExtension.class)
   class PaymentServiceTest {
       @Mock PaymentRepository repo;
       @InjectMocks PaymentService service;
       // TODO: add test methods
   }
   ```

6. **Report** files created and remind user to run `mvn test` or `./gradlew test`.
