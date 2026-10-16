from fastapi.testclient import TestClient


def test_healthz_answers_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_healthz_is_not_swallowed_by_the_ui_mount(client: TestClient) -> None:
    # The NiceGUI catch-all at "/" would answer an unknown path with HTML;
    # JSON here proves the route is registered before it.
    response = client.get("/healthz")
    assert response.headers["content-type"].startswith("application/json")
