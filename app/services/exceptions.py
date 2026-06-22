class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidOperationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
