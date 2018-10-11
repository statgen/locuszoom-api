import pytest
from flask import url_for
from locuszoom.api import create_app

@pytest.fixture(scope="session")
def client():
  app = create_app()
  client = app.test_client()
  return client
