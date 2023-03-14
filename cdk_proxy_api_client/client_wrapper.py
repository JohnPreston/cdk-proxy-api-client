#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from requests import Response

import re

from requests import delete, get, post, put
from requests.auth import HTTPBasicAuth

from .errors import evaluate_api_return


class ApiClient:
    """HTTP Calls wrapper"""

    json_headers: dict = {
        "Content-type": "application/json",
        "Accept": "application/json",
    }

    def __init__(
        self,
        hostname: str = None,
        port: int = None,
        url: str = None,
        protocol: str = None,
        ignore_ssl_errors: bool = False,
        username: str = None,
        password: str = None,
    ):
        """

        :param str hostname:
        :param int port: The endpoint port
        :param str protocol: http or https
        :param bool ignore_ssl_errors: Ignore SSL errors, for self-signed endpoints. Use at own risks
        :param str username: Username used for basic auth
        :param str password: Password used for basic auth
        """
        if (username and not password) or (password and not username):
            raise ValueError("You must specify both username and password")
        self.username = username
        self.password = password
        self.hostname = hostname

        self._url = None
        self._port = None
        self._protocol = "http"
        self._ignore_ssl_errors = ignore_ssl_errors

        self.protocol = protocol
        self.port = port
        self.url = url

    def __repr__(self):
        return self.url

    @property
    def verify_ssl(self) -> bool:
        if not self._ignore_ssl_errors and self.protocol == "http":
            return False
        return not self._ignore_ssl_errors

    @property
    def basic_auth(self) -> Union[HTTPBasicAuth, None]:
        """Returns basic auth information. If both the username and password are not set, raises AttributeError"""
        if self.username and self.password:
            return HTTPBasicAuth(self.username, self.password)
        if (self.username and not self.password) or (
            self.password and not self.username
        ):
            raise AttributeError("You must specify both username and password")
        return None

    @property
    def url(self) -> str:
        if self._url:
            return self._url
        elif self.hostname:
            if (self.port == 80 and self.protocol == "http") or (
                self.port == 443 and self.protocol == "https"
            ):
                return f"{self.protocol}://{self.hostname}"
            else:
                return f"{self.protocol}://{self.hostname}:{self.port}"
        else:
            raise AttributeError(
                "Unable to form a URL", self._url, self.hostname, self.port
            )

    @url.setter
    def url(self, value: Union[str, None]):
        if value is None:
            return
        if re.match(r"^https://(.*)$", value):
            self.protocol = "https"
        elif not re.match(r"(http://|https://)", value):
            print(f"URL Does not contain a protocol. Using default {self.protocol}")
            value = f"{self.protocol}://{value}"
        self._url = value

    @property
    def protocol(self) -> str:
        if self._protocol:
            return self._protocol
        return "http"

    @protocol.setter
    def protocol(self, value: Union[str, None]) -> None:
        if value is None:
            return
        valid_values: list = ["http", "https", "HTTP", "HTTPS"]
        if value not in valid_values:
            raise ValueError("protocol must be one of", valid_values, "got", value)
        self._protocol = value.lower()

    @property
    def port(self) -> int:
        if self._port:
            return self._port
        return 80

    @port.setter
    def port(self, value: Union[int, None]) -> None:
        if value is None and self.protocol == "http":
            value = 80
        elif value is None and self.protocol == "https":
            value = 443
        elif isinstance(value, str):
            value = int(value)

        if (value < 0) or (value > (2**16)):
            raise ValueError(
                f"Port {self.port} is not valid. Must be between 0 and {((2 ** 16) - 1)}"
            )
        self._port = value

    @evaluate_api_return
    def get(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = get(url, auth=self.basic_auth, verify=self.verify_ssl, **kwargs)
        return req

    @evaluate_api_return
    def post(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = post(
            url,
            auth=self.basic_auth,
            verify=self.verify_ssl,
            **kwargs,
        )
        return req

    @evaluate_api_return
    def put(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = put(
            url,
            auth=self.basic_auth,
            verify=self.verify_ssl,
            **kwargs,
        )
        return req

    @evaluate_api_return
    def delete(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = delete(url, auth=self.basic_auth, verify=self.verify_ssl, **kwargs)
        return req
