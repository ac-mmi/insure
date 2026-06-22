class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidOperationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class StateConflictError(Exception):
    """Raised when an operation conflicts with the current entity state."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
