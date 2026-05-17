---
name: go-codegen
description: >
  Triggered when a user asks to "scaffold a Go service", "add a handler", "create
  a repository interface", "generate a domain type", or requests new Go code from a
  story description with a Go project detected.
---

## Procedure

1. **Identify HTTP router** from `go.mod`: `chi`, `gin`, `echo`, or `net/http`.

2. **Generate domain type** in `internal/domain/`:
   ```go
   type Payment struct {
       ID        uuid.UUID
       Amount    decimal.Decimal
       Status    PaymentStatus
       CreatedAt time.Time
   }

   type PaymentStatus string
   const (
       PaymentStatusPending   PaymentStatus = "pending"
       PaymentStatusCompleted PaymentStatus = "completed"
   )
   ```

3. **Generate port interface** in `internal/port/`:
   ```go
   type PaymentStore interface {
       FindByID(ctx context.Context, id uuid.UUID) (*domain.Payment, error)
       Save(ctx context.Context, p *domain.Payment) error
   }
   ```

4. **Generate Postgres adapter** in `internal/adapter/postgres/`:
   ```go
   type pgPaymentStore struct{ db *pgxpool.Pool }

   func (s *pgPaymentStore) FindByID(ctx context.Context, id uuid.UUID) (*domain.Payment, error) {
       // pgx scan
   }
   func (s *pgPaymentStore) Save(ctx context.Context, p *domain.Payment) error {
       // pgx exec
   }
   ```

5. **Generate HTTP handler** in `internal/adapter/http/`:
   ```go
   func (h *PaymentHandler) CreatePayment(w http.ResponseWriter, r *http.Request) {
       var req CreatePaymentRequest
       if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
           http.Error(w, "bad request", http.StatusBadRequest)
           return
       }
       // call service, encode response
   }
   ```

6. **Generate test file**:
   ```go
   func TestCreatePayment(t *testing.T) {
       store := &mockPaymentStore{}
       handler := NewPaymentHandler(store)
       // table-driven test cases
   }
   ```

7. **Report** files created; remind user to run `go test ./... -race`.
