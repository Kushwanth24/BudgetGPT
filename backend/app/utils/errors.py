class AppError(Exception):
    def __init__(
        self,
        message: str,
        status: int = 400,
        code: str = "BAD_REQUEST",
        details: dict | None = None,
    ):
        self.message = message
        self.status = status
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self):
        return {
            "error": {
                "message": self.message,
                "code": self.code,
                "details": self.details,
            }
        }
