from flask import jsonify

def success_response(data=None, status_code=200):
    """Generate a standard success JSON response."""
    payload = {
        "success": True,
        "data": data if data is not None else {}
    }
    return jsonify(payload), status_code


def error_response(message="An error occurred", status_code=400):
    """Generate a standard error JSON response."""
    payload = {
        "success": False,
        "error": {
            "message": str(message)
        }
    }
    return jsonify(payload), status_code
