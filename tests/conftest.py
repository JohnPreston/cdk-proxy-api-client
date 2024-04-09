"""Pytest configuration and hooks"""

from os import path

import pytest
from testcontainers.compose import DockerCompose

HERE = path.abspath(path.dirname(__file__))


docker_compose = DockerCompose(
    path.abspath(f"{HERE}/.."),
    compose_file_name="docker-compose.yaml",
    wait=True,
    pull=True,
)

docker_compose.stop(down=True)
docker_compose.start()
gw_api_port = int(docker_compose.get_service_port("gateway", 8888))
base_url: str = f"http://localhost:{gw_api_port}"
docker_compose.wait_for(f"{base_url}/health")


@pytest.fixture(scope="session")
def kafka_bootstrap():
    return f"localhost:{docker_compose.get_service_port('broker', 9092)}"


@pytest.fixture(scope="session")
def gateway_bootstrap():
    bootstrap: str = ",".join(
        [
            f"localhost:{docker_compose.get_service_port('gateway', port)}"
            for port in [6969]
        ]
    )
    return bootstrap


@pytest.fixture(scope="session")
def base_url():
    gw_api_port = int(docker_compose.get_service_port("gateway", 8888))
    return f"http://localhost:{gw_api_port}"


def pytest_sessionfinish(session, exitstatus):
    docker_compose.stop()
    print()
    print("Testing session has finished")
    print(f"Exit status: {exitstatus}")
