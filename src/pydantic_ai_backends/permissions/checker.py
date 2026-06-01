"""Permission checker for validating operations against rulesets."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Literal

from typing_extensions import deprecated

from pydantic_ai_backends.permissions.types import (
    PermissionAction,
    PermissionOperation,
    PermissionRule,
    PermissionRuleset,
)

# Callback type for asking user permission
AskCallback = Callable[[PermissionOperation, str, str], Awaitable[bool]]

# Fallback behavior when ask_callback is not provided or returns None
AskFallback = Literal["deny", "error"]


class PermissionAskError(Exception):
    """Raised when a permission check fails with ask_fallback="error".

    Named `PermissionAskError` (not `PermissionError`) so it does not
    shadow the builtin `PermissionError` (an `OSError` subclass) for
    importers of this module.
    """

    def __init__(
        self,
        operation: PermissionOperation,
        target: str,
        reason: str = "",
    ):
        self.operation = operation
        self.target = target
        self.reason = reason
        message = f"Permission required for {operation} on '{target}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


@deprecated("Use `PermissionAskError` instead; this name shadows the builtin PermissionError.")
class PermissionError(PermissionAskError):
    """Deprecated alias for :class:`PermissionAskError`.

    Retained for backward compatibility. Prefer `PermissionAskError` to
    avoid shadowing the builtin `PermissionError`.
    """


class PermissionDeniedError(Exception):
    """Raised when a permission is explicitly denied."""

    def __init__(
        self,
        operation: PermissionOperation,
        target: str,
        rule: PermissionRule | None = None,
    ):
        self.operation = operation
        self.target = target
        self.rule = rule
        message = f"Permission denied for {operation} on '{target}'"
        if rule and rule.description:
            message += f": {rule.description}"
        super().__init__(message)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Convert a glob pattern to a regex pattern.

    Supports:
    - `*` matches any characters except `/`
    - `**` matches any characters including `/` (recursive)
    - `?` matches any single character except `/`
    - `[seq]` matches any character in seq
    """
    # Process the pattern character by character
    regex_parts: list[str] = []
    i = 0
    n = len(pattern)

    while i < n:
        c = pattern[i]

        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                # ** - match anything including /
                # Check if followed by /
                if i + 2 < n and pattern[i + 2] == "/":
                    # **/ - match zero or more directories
                    regex_parts.append("(?:.*/)?")
                    i += 3
                else:
                    # ** at end or before non-/
                    regex_parts.append(".*")
                    i += 2
            else:
                # Single * - match anything except /
                regex_parts.append("[^/]*")
                i += 1
        elif c == "?":
            # ? - match any single character except /
            regex_parts.append("[^/]")
            i += 1
        elif c == "[":
            # Character class - find the end
            j = i + 1
            negated = False
            if j < n and pattern[j] in "!^":
                # Glob negation uses '!'; regex negation uses '^'.
                negated = True
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j < n:
                # Valid character class. Emit '[^...]' for a negated class so
                # glob '[!a]' becomes regex '[^a]' (any char except 'a') rather
                # than the literal-matching '[!a]'.
                if negated:
                    inner = pattern[i + 2 : j]
                    regex_parts.append("[^" + inner + "]")
                else:
                    regex_parts.append(pattern[i : j + 1])
                i = j + 1
            else:
                # No closing bracket, treat as literal
                regex_parts.append(re.escape(c))
                i += 1
        else:
            # Escape other characters
            regex_parts.append(re.escape(c))
            i += 1

    regex_str = "^" + "".join(regex_parts) + "$"
    return re.compile(regex_str)


def _matches_pattern(target: str, pattern: str) -> bool:
    """Check if target matches the glob pattern.

    Args:
        target: The path or command to check.
        pattern: Glob pattern with optional ** support.

    Returns:
        True if target matches pattern.
    """
    regex = _glob_to_regex(pattern)
    return bool(regex.match(target))


class PermissionChecker:
    """Checks operations against a permission ruleset.

    The checker evaluates rules in order and uses the first matching rule's
    action. If no rule matches, the operation's default action is used.
    If no operation-specific permissions exist, the global default is used.

    Example:
        ```python
        from pydantic_ai_backends.permissions import (
            PermissionChecker,
            DEFAULT_RULESET,
        )

        async def ask_user(op: str, target: str, reason: str) -> bool:
            return input(f"Allow {op} on {target}? ").lower() == "y"

        checker = PermissionChecker(
            ruleset=DEFAULT_RULESET,
            ask_callback=ask_user,
        )

        # Synchronous check (returns action without asking)
        action = checker.check_sync("read", "/path/to/file")

        # Async check (handles "ask" via callback)
        allowed = await checker.check("write", "/path/to/file", "Save changes")
        ```
    """

    def __init__(
        self,
        ruleset: PermissionRuleset,
        ask_callback: AskCallback | None = None,
        ask_fallback: AskFallback = "error",
    ):
        """Initialize the permission checker.

        Args:
            ruleset: The permission ruleset to check against.
            ask_callback: Async callback for "ask" actions. Receives
                (operation, target, reason) and returns True to allow.
            ask_fallback: What to do when ask_callback is None or needed
                but not available. "deny" returns False, "error" raises.
        """
        self._ruleset = ruleset
        self._ask_callback = ask_callback
        self._ask_fallback = ask_fallback

    @property
    def ruleset(self) -> PermissionRuleset:
        """The permission ruleset being used."""
        return self._ruleset

    def check_sync(
        self,
        operation: PermissionOperation,
        target: str,
    ) -> PermissionAction:
        """Check permission synchronously without invoking callbacks.

        This method evaluates rules and returns the action without
        executing any callbacks. Use this when you need to know what
        action would be taken.

        Args:
            operation: The operation type (read, write, etc.).
            target: The path or command being accessed.

        Returns:
            The permission action: "allow", "deny", or "ask".
        """
        op_perms = self._ruleset.get_operation_permissions(operation)

        # Check rules in order - first match wins
        for rule in op_perms.rules:
            if _matches_pattern(target, rule.pattern):
                return rule.action

        # No rule matched, use default
        return op_perms.default

    def _find_matching_rule(
        self,
        operation: PermissionOperation,
        target: str,
    ) -> PermissionRule | None:
        """Find the first matching rule for an operation and target.

        Args:
            operation: The operation type.
            target: The path or command.

        Returns:
            The matching rule, or None if no rule matches.
        """
        op_perms = self._ruleset.get_operation_permissions(operation)

        for rule in op_perms.rules:
            if _matches_pattern(target, rule.pattern):
                return rule

        return None

    async def check(
        self,
        operation: PermissionOperation,
        target: str,
        reason: str = "",
    ) -> bool:
        """Check permission asynchronously with callback support.

        Evaluates rules and handles "ask" actions via the callback.
        For "allow" returns True, for "deny" raises PermissionDeniedError.

        Args:
            operation: The operation type (read, write, etc.).
            target: The path or command being accessed.
            reason: Human-readable reason for the operation.

        Returns:
            True if the operation is allowed.

        Raises:
            PermissionDeniedError: If the operation is explicitly denied.
            PermissionAskError: If ask_fallback="error" and callback unavailable.
        """
        action = self.check_sync(operation, target)

        if action == "allow":
            return True

        if action == "deny":
            rule = self._find_matching_rule(operation, target)
            raise PermissionDeniedError(operation, target, rule)

        # Action is "ask"
        if self._ask_callback is not None:
            allowed = await self._ask_callback(operation, target, reason)
            if allowed:
                return True
            raise PermissionDeniedError(operation, target)

        # No callback available
        if self._ask_fallback == "error":
            raise PermissionAskError(operation, target, reason)

        # ask_fallback == "deny"
        raise PermissionDeniedError(operation, target)

    def is_allowed(
        self,
        operation: PermissionOperation,
        target: str,
    ) -> bool:
        """Check if an operation would be immediately allowed.

        This is a convenience method that returns True only if the
        operation would be allowed without needing to ask.

        Args:
            operation: The operation type.
            target: The path or command.

        Returns:
            True if action is "allow", False otherwise.
        """
        return self.check_sync(operation, target) == "allow"

    def is_denied(
        self,
        operation: PermissionOperation,
        target: str,
    ) -> bool:
        """Check if an operation would be immediately denied.

        Args:
            operation: The operation type.
            target: The path or command.

        Returns:
            True if action is "deny", False otherwise.
        """
        return self.check_sync(operation, target) == "deny"

    def requires_approval(
        self,
        operation: PermissionOperation,
        target: str,
    ) -> bool:
        """Check if an operation would require user approval.

        Args:
            operation: The operation type.
            target: The path or command.

        Returns:
            True if action is "ask", False otherwise.
        """
        return self.check_sync(operation, target) == "ask"
