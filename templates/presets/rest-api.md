# Preset: REST API

Pre-filled user stories for a typical REST API feature. Customize for your specific resource.

## Pre-filled User Stories

### US-1: CRUD Operations

**As a** API consumer
**I want** to create, read, update, and delete {{RESOURCE}} via REST endpoints
**So that** I can manage {{RESOURCE}} data programmatically

#### Acceptance Criteria (EARS)

1. WHEN a POST request is sent to /api/{{resource}} with a valid body
   THE SYSTEM SHALL create the resource and return HTTP 201 with the created object including a generated ID

2. WHEN a GET request is sent to /api/{{resource}}/:id with a valid ID
   THE SYSTEM SHALL return HTTP 200 with the resource object

3. WHEN a GET request is sent to /api/{{resource}}/:id with a non-existent ID
   THE SYSTEM SHALL return HTTP 404 with an error object containing code "not_found"

4. WHEN a PUT request is sent to /api/{{resource}}/:id with a valid body
   THE SYSTEM SHALL update the resource and return HTTP 200 with the updated object

5. WHEN a DELETE request is sent to /api/{{resource}}/:id
   THE SYSTEM SHALL delete the resource and return HTTP 204

### US-2: Input Validation

**As a** API consumer
**I want** clear validation errors when I send invalid data
**So that** I can correct my requests

#### Acceptance Criteria (EARS)

1. WHEN a POST or PUT request is sent with missing required fields
   THE SYSTEM SHALL return HTTP 400 with an error object listing each missing field

2. WHEN a POST or PUT request is sent with fields of incorrect type
   THE SYSTEM SHALL return HTTP 400 with an error object specifying the type mismatch

### US-3: Authentication and Authorization

**As a** system administrator
**I want** only authorized users to access or modify resources
**So that** data is protected from unauthorized access

#### Acceptance Criteria (EARS)

1. WHEN a request is sent without a valid authentication token
   THE SYSTEM SHALL return HTTP 401 with an error object containing code "unauthorized"

2. WHEN an authenticated user attempts an action they lack permission for
   THE SYSTEM SHALL return HTTP 403 with an error object containing code "forbidden"

### US-4: Pagination and Filtering

**As a** API consumer
**I want** to paginate and filter resource listings
**So that** I can efficiently browse large datasets

#### Acceptance Criteria (EARS)

1. WHEN a GET request is sent to /api/{{resource}} with page and limit query parameters
   THE SYSTEM SHALL return the specified page of results with total count in response headers

2. WHEN a GET request is sent to /api/{{resource}} without pagination parameters
   THE SYSTEM SHALL return the first page with a default limit of 20 items

### US-5: Error Responses

**As a** API consumer
**I want** consistent, machine-readable error responses
**So that** I can programmatically handle errors

#### Acceptance Criteria (EARS)

1. THE SYSTEM SHALL return all errors as JSON objects with "code", "message", and "details" fields
2. THE SYSTEM SHALL NOT expose internal stack traces, database queries, or system paths in error responses
