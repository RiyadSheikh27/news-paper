"""utils/responses.py"""

from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """
    Standard success response format
    """
    return Response(
        {"success": True, "message": message, "data": data}, status=status_code
    )


def error_response(
    message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST
):
    """
    Standard error response format
    """
    return Response(
        {
            "success": False,
            "message": message,
            "data": None,
            "error": {"details": errors or message},
        },
        status=status_code,
    )


def created_response(data=None, message="Created successfully"):
    """
    Response for successful resource creation
    """
    return success_response(
        data=data, message=message, status_code=status.HTTP_201_CREATED
    )


def validation_error_response(errors):
    """
    Response for validation errors
    """
    return error_response(
        message="Validation failed",
        errors=errors,
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def not_found_response(message="Resource not found"):
    """
    Response for 404 errors
    """
    return error_response(message=message, status_code=status.HTTP_404_NOT_FOUND)
