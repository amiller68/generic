"""Chat module exceptions."""


class ThreadNotFound(Exception):
    """Thread does not exist or user doesn't have access."""

    pass


class CompletionNotFound(Exception):
    """Completion does not exist."""

    pass


class CompletionInProgress(Exception):
    """Thread already has an active completion."""

    pass


class ThreadCancelled(Exception):
    """Thread completion was cancelled by user."""

    pass
