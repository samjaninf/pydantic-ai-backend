# Permissions API

## Types

### PermissionAction

::: pydantic_ai_backends.permissions.types.PermissionAction
    options:
      show_root_heading: true

### PermissionOperation

::: pydantic_ai_backends.permissions.types.PermissionOperation
    options:
      show_root_heading: true

### PermissionRule

::: pydantic_ai_backends.permissions.types.PermissionRule
    options:
      show_root_heading: true
      members:
        - pattern
        - action
        - description

### OperationPermissions

::: pydantic_ai_backends.permissions.types.OperationPermissions
    options:
      show_root_heading: true
      members:
        - default
        - rules

### PermissionRuleset

::: pydantic_ai_backends.permissions.types.PermissionRuleset
    options:
      show_root_heading: true
      members:
        - default
        - read
        - write
        - edit
        - execute
        - glob
        - grep
        - ls
        - get_operation_permissions

## Checker

### PermissionChecker

::: pydantic_ai_backends.permissions.checker.PermissionChecker
    options:
      show_root_heading: true
      members:
        - __init__
        - check_sync
        - check
        - is_allowed
        - is_denied
        - requires_approval
        - ruleset

### PermissionAskError

Raised when a permission check resolves to `"ask"` but no `ask_callback` is
available and `ask_fallback="error"`.

::: pydantic_ai_backends.permissions.checker.PermissionAskError
    options:
      show_root_heading: true

### PermissionError

!!! warning "Deprecated"
    `PermissionError` is a deprecated alias for
    [`PermissionAskError`][pydantic_ai_backends.permissions.checker.PermissionAskError].
    It shadows the builtin `PermissionError`; use `PermissionAskError` instead.

::: pydantic_ai_backends.permissions.checker.PermissionError
    options:
      show_root_heading: true

### PermissionDeniedError

::: pydantic_ai_backends.permissions.checker.PermissionDeniedError
    options:
      show_root_heading: true

## Presets

### DEFAULT_RULESET

::: pydantic_ai_backends.permissions.presets.DEFAULT_RULESET
    options:
      show_root_heading: true

### PERMISSIVE_RULESET

::: pydantic_ai_backends.permissions.presets.PERMISSIVE_RULESET
    options:
      show_root_heading: true

### READONLY_RULESET

::: pydantic_ai_backends.permissions.presets.READONLY_RULESET
    options:
      show_root_heading: true

### STRICT_RULESET

::: pydantic_ai_backends.permissions.presets.STRICT_RULESET
    options:
      show_root_heading: true

### create_ruleset

::: pydantic_ai_backends.permissions.presets.create_ruleset
    options:
      show_root_heading: true

## Patterns

### SECRETS_PATTERNS

::: pydantic_ai_backends.permissions.presets.SECRETS_PATTERNS
    options:
      show_root_heading: true

### SYSTEM_PATTERNS

::: pydantic_ai_backends.permissions.presets.SYSTEM_PATTERNS
    options:
      show_root_heading: true

## Callback Types

### AskCallback

::: pydantic_ai_backends.permissions.checker.AskCallback
    options:
      show_root_heading: true

### AskFallback

::: pydantic_ai_backends.permissions.checker.AskFallback
    options:
      show_root_heading: true
