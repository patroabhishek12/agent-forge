---
name: rust-codegen
description: >
  Triggered when a user asks to "scaffold a Rust service", "add an axum handler",
  "create a repository trait", "generate a domain struct", or requests new Rust code
  from a story description with a Rust project detected.
---

## Procedure

1. **Identify web framework** from `Cargo.toml`: `axum`, `actix-web`, or `warp`.

2. **Generate domain struct** for the entity in `src/domain/`:
   ```rust
   #[derive(Debug, Clone, PartialEq)]
   pub struct Payment {
       pub id: Uuid,
       pub amount: Decimal,
       pub status: PaymentStatus,
       pub created_at: DateTime<Utc>,
   }

   #[derive(Debug, Clone, PartialEq)]
   pub enum PaymentStatus { Pending, Completed, Failed }
   ```

3. **Generate port trait** in `src/ports/`:
   ```rust
   #[async_trait]
   pub trait PaymentRepository: Send + Sync {
       async fn find_by_id(&self, id: Uuid) -> Result<Option<Payment>, Error>;
       async fn save(&self, payment: &Payment) -> Result<(), Error>;
   }
   ```

4. **Generate adapter** (sqlx example) in `src/adapters/`:
   ```rust
   pub struct PgPaymentRepository { pool: PgPool }

   #[async_trait]
   impl PaymentRepository for PgPaymentRepository {
       async fn find_by_id(&self, id: Uuid) -> Result<Option<Payment>, Error> {
           // sqlx query
       }
       async fn save(&self, payment: &Payment) -> Result<(), Error> {
           // sqlx query
       }
   }
   ```

5. **Generate axum handler** in `src/api/`:
   ```rust
   pub async fn create_payment(
       State(repo): State<Arc<dyn PaymentRepository>>,
       Json(body): Json<CreatePaymentRequest>,
   ) -> Result<Json<PaymentResponse>, AppError> {
       // validate, call domain, return
   }
   ```

6. **Generate unit test module** in the domain file:
   ```rust
   #[cfg(test)]
   mod tests {
       use super::*;
       // TODO: add tests
   }
   ```

7. **Report** files created; remind user to run `cargo test` and `cargo clippy`.
