# tests/conftest.py
import pytest
from unittest import mock

@pytest.fixture(autouse=True)
def mock_firebase_admin():
    with mock.patch("firebase_admin.credentials.Certificate"), \
         mock.patch("firebase_admin.initialize_app"), \
         mock.patch("firebase_admin.auth.verify_id_token", return_value={"uid": "mocked_uid", "email": "mock@example.com"}):
        yield
