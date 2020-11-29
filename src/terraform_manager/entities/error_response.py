import json
from typing import Dict, Any


class ErrorResponse:  # pragma: no cover
    """
    This class exists to satisfy a bare minimum of functionality of the requests.Response object. It
    will only be used in error scenarios when making HTTP requests.
    """
    def __init__(self, error_message: str):
        self.error_message = error_message
        self.status_code = 500

    def json(self) -> Dict[str, Any]:
        return {"terraform-manager": {"error": self.error_message, "status": self.status_code}}

    def __repr__(self):
        return json.dumps(self.json())

    def __str__(self):
        return repr(self)
