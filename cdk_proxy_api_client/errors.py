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
        super().__init__(details[0], code, details[1:])


class GenericConflict(ProxyGenericException):
    """Generic option for 409 return code"""

    def __init__(self, code, details):
        super().__init__(details[0], code, details[1:])


class GenericUnauthorized(ProxyGenericException):
    """Generic option for 401 return code"""

    def __init__(self, code, details):
        super().__init__(details[0], code, details[1:])


class GenericForbidden(ProxyGenericException):
    """Generic exception for a 403"""

    def __init__(self, code, details):
        super().__init__(details[0], code, details[1:])


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
        super().__init__(details[0], code, details[1])


def evaluate_api_return(function):
    """
    Decorator to evaluate the requests payload returned
    """

    def wrapped_answer(*args, **kwargs):
        """
        Decorator wrapper
        """
        print(args[0:2])
        try:
            payload = function(*args, **kwargs)
            if payload.status_code not in [200, 201, 202, 204] and not KEYISSET(
                "ignore_failure", kwargs
            ):
                try:
                    details = (args[0:2], payload.json())
                except req_exceptions.JSONDecodeError:
                    details = (args[0:2], payload.text)
                raise ProxyApiException(payload.status_code, details)

            elif KEYISSET("ignore_failure", kwargs):
                return payload
            return payload
        except req_exceptions.RequestException as error:
            print(error)
            raise

    return wrapped_answer
