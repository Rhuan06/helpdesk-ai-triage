from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


def _create_sample_ticket(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "Queda de conectividade no switch principal",
            "description": "Equipamentos do segundo andar perderam comunicação com a rede interna.",
            "requester_name": "Rafael",
            "category": "network",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    return response.json()


def _advance_ticket_to_status(client: TestClient, ticket_id: int, target_status: str) -> None:
    paths: dict[str, list[str]] = {
        "open": [],
        "in_analysis": ["in_analysis"],
        "in_progress": ["in_progress"],
        "resolved": ["in_progress", "resolved"],
        "closed": ["in_progress", "resolved", "closed"],
    }
    for step in paths[target_status]:
        res = client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": step})
        assert res.status_code == 200


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    [
        ("open", "in_analysis"),
        ("open", "in_progress"),
        ("open", "resolved"),
        ("open", "closed"),
        ("in_analysis", "in_progress"),
        ("in_analysis", "resolved"),
        ("in_analysis", "closed"),
        ("in_progress", "in_analysis"),
        ("in_progress", "resolved"),
        ("in_progress", "closed"),
        ("resolved", "in_progress"),
        ("resolved", "closed"),
    ],
)
def test_valid_status_transitions_succeed_with_200(
    client: TestClient,
    initial_status: str,
    target_status: str,
) -> None:
    ticket = _create_sample_ticket(client)
    ticket_id = ticket["id"]
    _advance_ticket_to_status(client, ticket_id, initial_status)

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": target_status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == target_status


@pytest.mark.parametrize(
    ("initial_status", "invalid_target"),
    [
        ("in_analysis", "open"),
        ("in_progress", "open"),
        ("resolved", "open"),
        ("resolved", "in_analysis"),
        ("closed", "open"),
        ("closed", "in_analysis"),
        ("closed", "in_progress"),
        ("closed", "resolved"),
    ],
)
def test_invalid_status_transitions_return_409_and_preserve_database_state(
    client: TestClient,
    initial_status: str,
    invalid_target: str,
) -> None:
    ticket = _create_sample_ticket(client)
    ticket_id = ticket["id"]
    _advance_ticket_to_status(client, ticket_id, initial_status)

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={
            "status": invalid_target,
            "priority": "low",
        },
    )

    assert response.status_code == 409

    # Verifica que nem o status nem a prioridade foram alterados no banco
    persisted = client.get(f"/api/v1/tickets/{ticket_id}").json()
    assert persisted["status"] == initial_status
    assert persisted["priority"] == "high"


def test_idempotent_same_status_update_is_allowed_for_active_ticket(
    client: TestClient,
) -> None:
    ticket = _create_sample_ticket(client)
    ticket_id = ticket["id"]
    _advance_ticket_to_status(client, ticket_id, "in_progress")

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={
            "status": "in_progress",
            "priority": "critical",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["priority"] == "critical"


@pytest.mark.parametrize(
    "patch_payload",
    [
        {"title": "Novo título indevido"},
        {"description": "Nova descrição indevida com mais de dez caracteres"},
        {"requester_name": "Outro Solicitante"},
        {"category": "software"},
        {"priority": "low"},
        {"status": "closed"},
        {"status": "in_progress"},
    ],
)
def test_closed_ticket_is_immutable_on_patch_and_preserves_state(
    client: TestClient,
    patch_payload: dict,
) -> None:
    ticket = _create_sample_ticket(client)
    ticket_id = ticket["id"]
    _advance_ticket_to_status(client, ticket_id, "closed")
    before_patch = client.get(f"/api/v1/tickets/{ticket_id}").json()

    response = client.patch(f"/api/v1/tickets/{ticket_id}", json=patch_payload)

    assert response.status_code == 409

    after_patch = client.get(f"/api/v1/tickets/{ticket_id}").json()
    assert after_patch == before_patch


def test_closed_ticket_blocks_reanalyze_with_409_without_calling_ai(
    client: TestClient,
    mock_ai_classifier: MagicMock,
) -> None:
    ticket = _create_sample_ticket(client)
    ticket_id = ticket["id"]
    _advance_ticket_to_status(client, ticket_id, "closed")
    before_analyze = client.get(f"/api/v1/tickets/{ticket_id}").json()

    calls_before = mock_ai_classifier.call_count
    response = client.post(f"/api/v1/tickets/{ticket_id}/analyze")

    assert response.status_code == 409
    assert mock_ai_classifier.call_count == calls_before

    after_analyze = client.get(f"/api/v1/tickets/{ticket_id}").json()
    assert after_analyze == before_analyze