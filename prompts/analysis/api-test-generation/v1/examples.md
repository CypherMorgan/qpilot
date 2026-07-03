Example: For a Pet Store API with these endpoints:

- GET /pets — List all pets
- POST /pets — Create a pet
- GET /pets/{petId} — Get a pet by ID
- DELETE /pets/{petId} — Delete a pet

And schemas:
- Pet: id (int, required), name (str, required), tag (str, optional)

Generate a test file like this:

```json
{
  "version": 1,
  "files": [
    {
      "filename": "test_pets.py",
      "content": "import pytest\nimport httpx\n\n\n@pytest.mark.asyncio\nasync def test_list_pets_happy_path(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"GET /pets should return a list of pets.\"\"\"\n    response = await client.get(\"/pets\", headers=auth_headers)\n    assert response.status_code == 200\n    data = response.json()\n    assert isinstance(data, list)\n    if data:\n        pet = data[0]\n        assert \"id\" in pet\n        assert \"name\" in pet\n\n\n@pytest.mark.asyncio\nasync def test_list_pets_with_limit(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"GET /pets with limit parameter should return at most that many items.\"\"\"\n    response = await client.get(\"/pets\", headers=auth_headers, params={\"limit\": 5})\n    assert response.status_code == 200\n    data = response.json()\n    assert isinstance(data, list)\n    assert len(data) <= 5\n\n\n@pytest.mark.asyncio\nasync def test_list_pets_unauthorized(\n    client: httpx.AsyncClient,\n) -> None:\n    \"\"\"GET /pets without auth headers should return 401.\"\"\"\n    response = await client.get(\"/pets\")\n    assert response.status_code == 401\n\n\n@pytest.mark.asyncio\nasync def test_create_pet_happy_path(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"POST /pets with valid data should create a pet.\"\"\"\n    payload = {\"name\": \"Buddy\", \"tag\": \"dog\"}\n    response = await client.post(\"/pets\", json=payload, headers=auth_headers)\n    assert response.status_code == 201\n    data = response.json()\n    assert \"id\" in data\n    assert data[\"name\"] == \"Buddy\"\n\n\n@pytest.mark.asyncio\nasync def test_create_pet_missing_name(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"POST /pets without required 'name' field should return 400.\"\"\"\n    payload = {\"tag\": \"dog\"}\n    response = await client.post(\"/pets\", json=payload, headers=auth_headers)\n    assert response.status_code == 400\n\n\n@pytest.mark.asyncio\nasync def test_get_pet_by_id_happy_path(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"GET /pets/{petId} should return a single pet.\"\"\"\n    response = await client.get(\"/pets/1\", headers=auth_headers)\n    assert response.status_code == 200\n    data = response.json()\n    assert data[\"id\"] == 1\n    assert \"name\" in data\n\n\n@pytest.mark.asyncio\nasync def test_get_pet_not_found(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"GET /pets/{petId} with non-existent ID should return 404.\"\"\"\n    response = await client.get(\"/pets/99999\", headers=auth_headers)\n    assert response.status_code == 404\n\n\n@pytest.mark.asyncio\nasync def test_get_pet_invalid_id(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"GET /pets/{petId} with non-integer ID should return 422.\"\"\"\n    response = await client.get(\"/pets/abc\", headers=auth_headers)\n    assert response.status_code == 422\n\n\n@pytest.mark.asyncio\nasync def test_delete_pet_happy_path(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"DELETE /pets/{petId} should delete and return 204.\"\"\"\n    response = await client.delete(\"/pets/1\", headers=auth_headers)\n    assert response.status_code == 204\n\n\n@pytest.mark.asyncio\nasync def test_delete_pet_not_found(\n    client: httpx.AsyncClient,\n    auth_headers: dict,\n) -> None:\n    \"\"\"DELETE /pets/{petId} with non-existent ID should return 404.\"\"\"\n    response = await client.delete(\"/pets/99999\", headers=auth_headers)\n    assert response.status_code == 404\n"
    }
  ]
}
```

Generate 3-8 test functions per endpoint, covering at minimum: happy path, error handling for each documented error code, and schema validation.
