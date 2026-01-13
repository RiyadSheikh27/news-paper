"""news/utils.py"""
import hashlib


def get_user_identifier(request):
    """
    Generate a unique identifier for the user based on browser fingerprint
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

    # Create a hash from these values
    fingerprint_string = f"{user_agent}|{ip_address}|{accept_language}|{accept_encoding}"
    user_identifier = hashlib.sha256(fingerprint_string.encode()).hexdigest()

    return user_identifier


def get_client_ip(request):
    """
    Get the client's IP address from the request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_read_news_ids(request):
    """
    Get list of read news IDs from request header or cookie
    The client should send read news IDs in header like: X-Read-News: 1,2,3,4
    """
    read_news_header = request.META.get('HTTP_X_READ_NEWS', '')
    if read_news_header:
        try:
            return [int(id.strip()) for id in read_news_header.split(',') if id.strip().isdigit()]
        except (ValueError, AttributeError):
            return []
    return []