from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_create_ticket_preserves_official_fields_and_populates_ai_fields(
    client: TestClient,
    mock_ai_classifier: MagicMock,
) -> None:
    payload = {
        "title": "Sem acesso ao sistema ERP",
        "description": "Ao tentar autenticar no ERP interno, ocorre erro de timeout.",
        "requester_name": "Mariana Costa",
        "category": "software",
        "priority": "low",
    }

    response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Sem acesso ao sistema ERP"
    assert data["description"] == "Ao tentar autenticar no ERP interno, ocorre erro de timeout."
    assert data["requester_name"] == "Mariana Costa"
    # Campos oficiais preservados sem sobrescrita pela IA
    assert data["category"] == "software"
    assert data["priority"] == "low"
    assert data["status"] == "open"
    # Campos de sugestão preenchidos pela IA
    assert data["ai_suggested_category"] == "network"
    assert data["ai_suggested_priority"] == "high"
    assert data["ai_technical_summary"] is not None
    assert len(data["ai_possible_causes"]) == 2
    assert len(data["ai_suggested_resolution"]) == 2
    assert "created_at" in data
    assert "updated_at" in data
    mock_ai_classifier.assert_called_once_with(
        title="Sem acesso ao sistema ERP",
        description="Ao tentar autenticar no ERP interno, ocorre erro de timeout.",
    )


def test_create_ticket_applies_default_category_and_priority(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "Monitor piscando",
            "description": "O monitor secundário apresenta falhas intermitentes de imagem.",
            "requester_name": "Carlos",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "other"
    assert data["priority"] == "medium"
    assert data["status"] == "open"


def test_create_ticket_strips_whitespace_on_text_fields(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "   Impressora travada na fila   ",
            "description": "   Documentos enviados para impressão ficam retidos sem erro.   ",
            "requester_name": "  Ana Paula  ",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Impressora travada na fila"
    assert data["description"] == "Documentos enviados para impressão ficam retidos sem erro."
    assert data["requester_name"] == "Ana Paula"


def test_create_ticket_rejects_blank_or_invalid_inputs_with_422(
    client: TestClient,
    mock_ai_classifier: MagicMock,
) -> None:
    invalid_payloads = [
        # Campos apenas com espaços em branco
        {
            "title": "     ",
            "description": "Descrição válida com tamanho suficiente.",
            "requester_name": "Rhuan",
        },
        {
            "title": "Título válido",
            "description": "          ",
            "requester_name": "Rhuan",
        },
        {
            "title": "Título válido",
            "description": "Descrição válida com tamanho suficiente.",
            "requester_name": "   ",
        },
        # Campos abaixo do min_length após strip
        {
            "title": " ab ",
            "description": "Descrição válida com tamanho suficiente.",
            "requester_name": "Rhuan",
        },
        # Enum inválido
        {
            "title": "Título válido",
            "description": "Descrição válida com tamanho suficiente.",
            "requester_name": "Rhuan",
            "category": "invalid_category",
        },
        # Campo obrigatório ausente
        {
            "title": "Título válido",
            "requester_name": "Rhuan",
        },
    ]

    for payload in invalid_payloads:
        response = client.post("/api/v1/tickets", json=payload)
        assert response.status_code == 422

    assert mock_ai_classifier.call_count == 0


def test_list_tickets_supports_filters_and_pagination(
    client: TestClient,
) -> None:
    tickets_to_create = [
        {
            "title": "Chamado Rede 1",
            "description": "Queda de link na filial sul durante o expediente.",
            "requester_name": "User 1",
            "category": "network",
            "priority": "high",
        },
        {
            "title": "Chamado Hardware 2",
            "description": "Teclado com teclas falhando na estação de trabalho.",
            "requester_name": "User 2",
            "category": "hardware",
            "priority": "low",
        },
        {
            "title": "Chamado Rede 3",
            "description": "Latência elevada no acesso ao servidor de arquivos.",
            "requester_name": "User 3",
            "category": "network",
            "priority": "high",
        },
    ]

    created_ids = []
    for item in tickets_to_create:
        res = client.post("/api/v1/tickets", json=item)
        assert res.status_code == 201
        created_ids.append(res.json()["id"])

    # Move o primeiro chamado para in_progress para testar filtro por status
    patch_res = client.patch(
        f"/api/v1/tickets/{created_ids[0]}",
        json={"status": "in_progress"},
    )
    assert patch_res.status_code == 200

    # Listagem completa
    all_res = client.get("/api/v1/tickets")
    assert all_res.status_code == 200
    assert len(all_res.json()) == 3

    # Filtro combinado por category e priority
    filtered_res = client.get(
        "/api/v1/tickets",
        params={"category": "network", "priority": "high"},
    )
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()
    assert len(filtered_data) == 2
    assert all(t["category"] == "network" and t["priority"] == "high" for t in filtered_data)

    # Filtro por status
    status_res = client.get("/api/v1/tickets", params={"status": "in_progress"})
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert len(status_data) == 1
    assert status_data[0]["id"] == created_ids[0]

    # Paginação (skip e limit)
    page_res = client.get("/api/v1/tickets", params={"skip": 1, "limit": 1})
    assert page_res.status_code == 200
    assert len(page_res.json()) == 1


def test_get_ticket_by_id_returns_200_and_404_when_missing(
    client: TestClient,
) -> None:
    create_res = client.post(
        "/api/v1/tickets",
        json={
            "title": "Erro de permissão em pasta",
            "description": "Acesso negado ao diretório compartilhado do financeiro.",
            "requester_name": "Lucas",
        },
    )
    ticket_id = create_res.json()["id"]

    found_res = client.get(f"/api/v1/tickets/{ticket_id}")
    assert found_res.status_code == 200
    assert found_res.json()["id"] == ticket_id

    missing_res = client.get("/api/v1/tickets/9999")
    assert missing_res.status_code == 404


def test_update_ticket_partial_and_validation_errors(
    client: TestClient,
) -> None:
    create_res = client.post(
        "/api/v1/tickets",
        json={
            "title": "Falha no cliente de e-mail",
            "description": "Aplicativo fecha sozinho ao abrir anexos grandes.",
            "requester_name": "Beatriz",
            "category": "software",
            "priority": "medium",
        },
    )
    ticket_id = create_res.json()["id"]

    # Atualização parcial válida com strip()
    patch_res = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={
            "title": "  Falha crítica no cliente de e-mail  ",
            "priority": "critical",
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["title"] == "Falha crítica no cliente de e-mail"
    assert updated["priority"] == "critical"
    assert updated["category"] == "software"
    assert updated["status"] == "open"

    # Rejeição de string apenas com espaços no PATCH -> 422
    blank_res = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"title": "    "},
    )
    assert blank_res.status_code == 422

    # Rejeição de campo explicitamente nulo no PATCH -> 422
    null_res = client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"priority": None},
    )
    assert null_res.status_code == 422

    # ID inexistente -> 404
    missing_res = client.patch(
        "/api/v1/tickets/9999",
        json={"priority": "low"},
    )
    assert missing_res.status_code == 404


def test_delete_ticket_returns_204_and_404_when_missing(
    client: TestClient,
) -> None:
    create_res = client.post(
        "/api/v1/tickets",
        json={
            "title": "Solicitação de acesso VPN",
            "description": "Configurar credenciais VPN para trabalho remoto.",
            "requester_name": "Fernanda",
        },
    )
    ticket_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/tickets/{ticket_id}")
    assert del_res.status_code == 204
    assert del_res.content == b""

    get_after_del = client.get(f"/api/v1/tickets/{ticket_id}")
    assert get_after_del.status_code == 404

    del_missing = client.delete(f"/api/v1/tickets/{ticket_id}")
    assert del_missing.status_code == 404