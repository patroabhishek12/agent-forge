---
id: react-conventions
description: React/TypeScript SPA conventions and component structure rules
apply_to: ["**/*.tsx", "**/*.ts", "src/**/*.jsx", "src/**/*.js"]
---

## Naming
- Components: `PascalCase` filenames and function names.
- Hooks: `useXxx` prefix. Utilities: `camelCase`. Constants: `UPPER_SNAKE_CASE`.
- CSS modules: `ComponentName.module.css`. Styled-components: co-locate in same file.

## Project structure
```
src/
  components/         — reusable, stateless/lightly-stateful UI pieces
  features/           — feature slices (each has its own components/, hooks/, api/)
  hooks/              — shared custom hooks
  lib/                — pure utility functions, no React
  api/                — API client functions (React Query queries/mutations)
  store/              — global state (Zustand / Redux Toolkit slices)
  types/              — shared TypeScript types and interfaces
  pages/ (or routes/) — route-level components
  App.tsx, main.tsx   — root
```

## Component rules
- Prefer function components with hooks. No class components in new code.
- One component per file. Keep files under 200 lines; split if larger.
- Props interface defined above the component: `interface ButtonProps { ... }`.
- Default exports for page/route components; named exports for shared components.
- Avoid prop drilling beyond 2 levels — use context or store.

## State management
- Local UI state: `useState` / `useReducer`.
- Server state: React Query (`useQuery`, `useMutation`). No manual fetch in components.
- Global app state: Zustand (preferred) or Redux Toolkit. No Redux for server data.

## TypeScript
- Strict mode enabled (`"strict": true` in tsconfig).
- Never use `any`. Prefer `unknown` and narrow explicitly.
- Use `satisfies` operator for type-safe object literals.

## Testing
- Unit: Vitest + React Testing Library. Render via `renderWithProviders` wrapper.
- Interaction tests: test user behaviour, not implementation details.
- E2E: Playwright tests in `e2e/` directory.
- Coverage target: 75% on `features/` and `hooks/`.
