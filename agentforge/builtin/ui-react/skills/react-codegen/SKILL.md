---
name: react-codegen
description: >
  Triggered when a user asks to "create a React component", "scaffold a feature",
  "add a page", "build the UI for this story", or requests new React/TypeScript code
  from a story description with a React/SPA project detected.
---

## Procedure

1. **Identify state library** from `package.json`: Zustand, Redux Toolkit, or Context API.
   Identify data-fetching library: React Query (TanStack), SWR, or RTK Query.

2. **Determine what to generate** from the story:
   - Feature slice (full: component + hook + api + types)
   - Standalone component
   - Custom hook
   - API query/mutation

3. **Generate types** in `src/features/<feature>/types.ts`:
   ```typescript
   export interface Payment {
     id: string;
     amount: number;
     status: 'pending' | 'completed' | 'failed';
     createdAt: string;
   }

   export interface CreatePaymentRequest {
     amount: number;
     currency: string;
   }
   ```

4. **Generate API layer** in `src/features/<feature>/api.ts` (React Query example):
   ```typescript
   export function usePayments() {
     return useQuery({ queryKey: ['payments'], queryFn: fetchPayments });
   }

   export function useCreatePayment() {
     const queryClient = useQueryClient();
     return useMutation({
       mutationFn: (body: CreatePaymentRequest) => api.post('/payments', body),
       onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payments'] }),
     });
   }
   ```

5. **Generate component** in `src/features/<feature>/components/`:
   ```tsx
   interface PaymentListProps { onSelect: (id: string) => void; }

   export function PaymentList({ onSelect }: PaymentListProps) {
     const { data, isLoading } = usePayments();
     if (isLoading) return <Spinner />;
     return (
       <ul>
         {data?.map((p) => (
           <li key={p.id} onClick={() => onSelect(p.id)}>{p.amount}</li>
         ))}
       </ul>
     );
   }
   ```

6. **Generate test** alongside component:
   ```typescript
   it('renders payment list', async () => {
     renderWithProviders(<PaymentList onSelect={vi.fn()} />);
     expect(await screen.findByRole('list')).toBeInTheDocument();
   });
   ```

7. **Register the route** — add an entry in the router config if a page was created.

8. **Report** files created and remind user to run `npm test` / `pnpm test`.
