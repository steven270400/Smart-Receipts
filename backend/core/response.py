def success_response(data=None, message: str = "success") -> dict:
    return {
        "code": 0,
        "message": message,
        "data": data,
    }


def error_response(code: int, message: str, data=None) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
    }
