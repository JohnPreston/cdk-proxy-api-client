#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2023 John Mille <john@ews-network.net>

from requests import exceptions as req_exceptions

KEYISSET = lambda key, obj: isinstance(obj, dict) and key in obj and obj[key]


class ProxyGenericException(Exception):
    """Generic class handling Exceptions"""

    def __init__(self, msg, code, details):
        super().__init__(msg, code, details)
        self.code = code
        self.details = details


class GenericNotFound(ProxyGenericException):
    """Generic option for 404 return code"""

    def __init__(self, code, details):
        super().__init__(details.get("detail", "Resource not found"), code, details)


class GenericConflict(ProxyGenericException):
    """Generic option for 409 return code"""

    def __init__(self, code, details):
        super().__init__(details.get("detail", "Resources conflict"), code, details)


class GenericUnauthorized(ProxyGenericException):
    """Generic option for 401 return code"""

    def __init__(self, code, details):
        super().__init__(details.get("detail", "Access unauthorized"), code, details)


class GenericForbidden(ProxyGenericException):
    """Generic exception for a 403"""

    def __init__(self, code, details):
        super().__init__(details.get("detail", "403 Forbidden"), code, details)


class ProxyApiException(ProxyGenericException):
    def __init__(self, code, details):
        if code == 409:
            raise GenericConflict(code, details)
        elif code == 404:
            raise GenericNotFound(code, details)
        elif code == 401:
            raise GenericUnauthorized(code, details)
        elif code == 403:
            raise GenericForbidden(code, details)
        super().__init__("Something was wrong with the client request.", code, details)


def evaluate_api_return(function):
    """
    Decorator to evaluate the requests payload returned
    """

    def wrapped_answer(*args, **kwargs):
        """
        Decorator wrapper
        """
        try:
            payload = function(*args, **kwargs)
            if payload.status_code not in [200, 201, 202, 204] and not KEYISSET(
                "ignore_failure", kwargs
            ):
                details = payload.json()
                raise ProxyApiException(payload.status_code, details)

            elif KEYISSET("ignore_failure", kwargs):
                return payload
            return payload
        except req_exceptions.RequestException as error:
            print(error)
            raise

    return wrapped_answer
