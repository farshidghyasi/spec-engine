# EARS Notation Reference

Easy Approach to Requirements Syntax (EARS) provides five patterns for writing unambiguous, testable requirements.

## The Five EARS Patterns

### 1. Ubiquitous (always true)

No trigger or condition. The system must always exhibit this behavior.

```
THE SYSTEM SHALL [behavior]
```

**Examples:**
- THE SYSTEM SHALL encrypt all data at rest using AES-256
- THE SYSTEM SHALL log all API requests with timestamp, method, path, and response status
- THE SYSTEM SHALL NOT store plaintext passwords

### 2. Event-Driven (triggered by action)

Behavior in response to a specific trigger or event.

```
WHEN [trigger]
THE SYSTEM SHALL [behavior]
```

**Examples:**
- WHEN the user clicks the "Save" button
  THE SYSTEM SHALL validate the form and persist the data to the database

- WHEN a POST request is sent to /api/users with a valid body
  THE SYSTEM SHALL create the user and return HTTP 201

### 3. State-Driven (while in a state)

Behavior that applies while the system is in a particular state.

```
WHILE [state]
THE SYSTEM SHALL [behavior]
```

**Examples:**
- WHILE the user is on the checkout page
  THE SYSTEM SHALL display the order total in the sidebar

- WHILE the system is in maintenance mode
  THE SYSTEM SHALL return HTTP 503 for all API requests with a "retry-after" header

### 4. Conditional (if condition, when trigger)

Behavior that depends on both a precondition AND a trigger.

```
IF [condition]
WHEN [trigger]
THE SYSTEM SHALL [behavior]
```

**Examples:**
- IF the user has admin role
  WHEN they access the /admin route
  THE SYSTEM SHALL display the admin dashboard

- IF the cart contains items over $100
  WHEN the user proceeds to checkout
  THE SYSTEM SHALL apply free shipping automatically

### 5. Feature-Specific (WHERE)

Behavior limited to a specific feature, variant, or context.

```
WHERE [feature/context]
WHEN [trigger]
THE SYSTEM SHALL [behavior]
```

**Examples:**
- WHERE the premium plan is active
  WHEN the user requests an export
  THE SYSTEM SHALL offer CSV, JSON, and PDF formats

- WHERE the mobile app is used
  WHEN the user swipes left on a list item
  THE SYSTEM SHALL reveal the delete action

## Composing Patterns

Patterns can be composed for complex requirements:

```
WHILE [state]
IF [condition]
WHEN [trigger]
THE SYSTEM SHALL [behavior]
```

**Example:**
- WHILE the user is authenticated
  IF they have editor permissions
  WHEN they submit a document for review
  THE SYSTEM SHALL create a review request and notify all reviewers via email

## Negative Requirements

Add "NOT" to any pattern to specify what the system must NOT do:

```
THE SYSTEM SHALL NOT [prohibited behavior]

WHEN [trigger]
THE SYSTEM SHALL NOT [prohibited behavior]
```

**Examples:**
- THE SYSTEM SHALL NOT expose internal error details in API responses
- WHEN a user account is deactivated
  THE SYSTEM SHALL NOT allow login attempts to succeed

## Quality Rules

1. **One behavior per requirement.** Split compound behaviors into separate ACs.
2. **No vague terms.** Avoid: quickly, easily, properly, user-friendly, intuitive, reasonable, appropriate, efficient, robust, seamless, flexible, scalable (without metrics).
3. **Testable.** Every AC must have a deterministic pass/fail test.
4. **Error paths required.** For each WHEN trigger, include an AC for when the trigger fails or the input is invalid.
5. **Specific observables.** State what the user sees or what the API returns, not internal implementation details.
