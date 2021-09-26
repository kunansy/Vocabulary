import time

import pytest


@pytest.fixture(scope="function")
def sleep():
    time.sleep(3)
