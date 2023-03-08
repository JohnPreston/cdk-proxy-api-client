#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import TYPE_CHECKING

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
        self.hostname = hostname
        self.protocol = protocol if protocol else "http"
        self.verify_ssl = not ignore_ssl_errors
        self.port = port if port else 8083
        self.username = username
        self.password = password

        if self.protocol not in ["http", "https"]:
            raise ValueError("protocol must be one of", ["http", "https"])
        if (self.port < 0) or (self.port > (2**16)):
            raise ValueError(
                f"Port {self.port} is not valid. Must be between 0 and {((2 ** 16) - 1)}"
            )
        if self.username and not self.password or self.password and not self.username:
            raise ValueError("You must specify both username and password")
        if self.verify_ssl is True and self.protocol == "http":
            print("No SSL needed for HTTP without TLS. Disabling")
            self.verify_ssl = False
        if url:
            self.url = url
            if not re.match(r"(http://|https://)", self.url):
                print(f"URL Does not contain a protocol. Using default {self.protocol}")
                self.url = f"{self.protocol}://{self.url}"
            print("URL Defined from parameter. Skipping hostname:port parameters")
        elif (self.port == 80 and protocol == "http") or (
            self.port == 443 and self.protocol == "https"
        ):
            self.url = f"{self.protocol}://{self.hostname}"
        else:
            self.url = f"{self.protocol}://{self.hostname}:{self.port}"

        self.auth = (
            HTTPBasicAuth(self.username, self.password)
            if self.username and self.password
            else None
        )

        self.headers = {
            # "Content-type": "application/json",
            # "Accept": "application/json",
        }

    def __repr__(self):
        return self.url

    @evaluate_api_return
    def get_raw(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = get(
            url, auth=self.auth, headers=self.headers, verify=self.verify_ssl, **kwargs
        )
        return req

    def get(self, query_path, **kwargs):
        req = self.get_raw(query_path, **kwargs)
        return req.json()

    @evaluate_api_return
    def post_raw(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = post(
            url,
            auth=self.auth,
            headers=self.headers,
            verify=self.verify_ssl,
            **kwargs,
        )
        return req

    def post(self, query_path, **kwargs):
        req = self.post_raw(query_path, **kwargs)
        return req.json()

    @evaluate_api_return
    def put_raw(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = put(
            url,
            auth=self.auth,
            headers=self.headers,
            verify=self.verify_ssl,
            **kwargs,
        )
        return req

    def put(self, query_path, **kwargs):
        req = self.put_raw(query_path, **kwargs)
        return req.json()

    @evaluate_api_return
    def delete_raw(self, query_path, **kwargs) -> Response:
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = delete(
            url, auth=self.auth, headers=self.headers, verify=self.verify_ssl, **kwargs
        )
        return req

    def delete(self, query_path):
        req = self.delete_raw(query_path)
        return req.json()
