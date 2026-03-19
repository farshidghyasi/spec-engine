# Design Patterns Reference

Guidance for the spec-planner agent when writing design.md.

## Component Design

### Interface Contracts

Every component must define its interface with precise type signatures, not English descriptions:

```typescript
// Good: precise contract
interface UserService {
  getById(id: string): Promise<User | null>;
  create(data: CreateUserDTO): Promise<User>;
  update(id: string, data: Partial<CreateUserDTO>): Promise<User>;
  delete(id: string): Promise<void>;
}

// Bad: vague contract
// UserService handles user operations
```

### Traceability

Every component MUST include a `Covers: US-X` annotation listing which user stories it implements. This enables:
- Validator to check all requirements are covered
- Impact analysis when requirements change
- Acceptance testing traceability

## Error Handling Strategy

### Error Taxonomy Template

| Error Class | Examples | HTTP Status | User Message | Log Level |
|------------|----------|-------------|--------------|-----------|
| Validation | Missing fields, wrong types | 400 | Specific field errors | warn |
| Authentication | Missing/expired token | 401 | "Please sign in" | info |
| Authorization | Insufficient permissions | 403 | "You don't have access" | warn |
| Not Found | Resource doesn't exist | 404 | "Not found" | info |
| Conflict | Duplicate, concurrent edit | 409 | Specific conflict details | warn |
| Internal | Unexpected exceptions | 500 | "Something went wrong" | error |

### Error Propagation Rules

1. **Never leak internals.** No stack traces, SQL queries, file paths, or env vars in responses.
2. **Be specific in logs, generic in responses.** Log the full error; return a safe message.
3. **Consistent format.** All errors must use the same JSON shape: `{ code, message, details }`.
4. **Fail fast.** Validate inputs at the boundary before processing.

## State Management

### When to Document State

Include a State Management section when the feature involves:
- Multi-step workflows (wizards, checkout flows)
- Real-time data (websockets, polling)
- Optimistic updates
- Offline-capable features
- Complex form state

### State Diagram Template

```
[Initial] --user action--> [Loading]
[Loading] --success------> [Loaded]
[Loading] --failure------> [Error]
[Error]   --retry--------> [Loading]
[Loaded]  --user action--> [Saving]
[Saving]  --success------> [Loaded]
[Saving]  --failure------> [Error]
```

## API Design

### REST Conventions

| Operation | Method | Path | Success | Failure |
|-----------|--------|------|---------|---------|
| List | GET | /resources | 200 + array | 400 (bad params) |
| Create | POST | /resources | 201 + object | 400 (validation) |
| Read | GET | /resources/:id | 200 + object | 404 |
| Update | PUT | /resources/:id | 200 + object | 404, 400 |
| Delete | DELETE | /resources/:id | 204 | 404 |

### Pagination

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

## Data Model Design

### Constraints Checklist

For each model field, consider:
- Required vs optional?
- Min/max length or value?
- Unique constraint?
- Foreign key relationship?
- Default value?
- Indexed for query performance?

## Security Considerations

Every design should address:
1. **Authentication**: How are users identified?
2. **Authorization**: How are permissions checked?
3. **Input validation**: Where are inputs sanitized?
4. **Data protection**: What is encrypted? At rest? In transit?
5. **Rate limiting**: How are abuse scenarios prevented?
6. **Audit logging**: What security-relevant events are logged?
