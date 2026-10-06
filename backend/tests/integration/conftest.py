from uuid import uuid4

import pytest


@pytest.fixture(autouse=True)
def authenticated_integration_client(request):
    if request.module.__name__.endswith("test_auth"):
        yield
        return
    client = getattr(request.module, "client", None)
    if client is not None:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid4().hex}@example.com", "password": "correct-horse-battery"},
        )
        assert response.status_code == 201
        client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    yield
