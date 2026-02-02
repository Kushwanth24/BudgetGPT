class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def error_response(message: str, status_code: int = 400, details=None):
    payload = {"error": message}
    if details is not None:
        payload["details"] = details
    return payload, status_code
