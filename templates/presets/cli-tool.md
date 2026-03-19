# Preset: CLI Tool

Pre-filled user stories for a typical command-line tool. Customize for your specific CLI.

## Pre-filled User Stories

### US-1: Argument Parsing

**As a** CLI user
**I want** to pass arguments and flags to the command
**So that** I can control the tool's behavior

#### Acceptance Criteria (EARS)

1. WHEN the user runs the command with valid arguments
   THE SYSTEM SHALL parse and validate each argument before executing

2. WHEN the user passes an unknown flag or invalid argument
   THE SYSTEM SHALL print a descriptive error message and exit with code 1

3. WHEN the user passes --help or -h
   THE SYSTEM SHALL print usage information with all available flags and exit with code 0

4. WHEN the user passes --version or -v
   THE SYSTEM SHALL print the version number and exit with code 0

### US-2: Subcommands

**As a** CLI user
**I want** to use subcommands for different operations
**So that** related functionality is organized logically

#### Acceptance Criteria (EARS)

1. WHEN the user runs a valid subcommand
   THE SYSTEM SHALL execute the corresponding operation with its own argument parsing

2. WHEN the user runs an unknown subcommand
   THE SYSTEM SHALL print "Unknown command: <name>" and suggest similar commands if available

3. WHEN the user runs the command without a subcommand
   THE SYSTEM SHALL print the help text listing all available subcommands

### US-3: Output Formatting

**As a** CLI user
**I want** clear, well-formatted output
**So that** I can read results and pipe them to other tools

#### Acceptance Criteria (EARS)

1. WHEN the --json flag is provided
   THE SYSTEM SHALL output results as valid JSON to stdout

2. WHEN stdout is a TTY (interactive terminal)
   THE SYSTEM SHALL use colors and formatting for readability

3. WHEN stdout is piped to another command
   THE SYSTEM SHALL output plain text without colors or special formatting

### US-4: Error Handling

**As a** CLI user
**I want** clear error messages that help me fix issues
**So that** I can resolve problems without reading source code

#### Acceptance Criteria (EARS)

1. WHEN an error occurs
   THE SYSTEM SHALL print a human-readable error message to stderr and exit with a non-zero code

2. THE SYSTEM SHALL NOT print stack traces unless --debug or --verbose flag is provided

3. WHEN the tool cannot connect to a required external service
   THE SYSTEM SHALL print which service is unreachable and suggest troubleshooting steps
