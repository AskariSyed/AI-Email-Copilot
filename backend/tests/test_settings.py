def test_get_settings_not_found(client):
    # User 1 has no settings initially
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    assert response.json() == {"profile_data": {}}

def test_save_settings(client):
    # Save new settings
    new_settings = {
        "profile_data": {
            "instructions": "Be very concise and polite.",
            "tone": "professional"
        }
    }
    response = client.post("/api/v1/settings", json=new_settings)
    assert response.status_code == 200
    assert "profile_data" in response.json()

def test_get_settings_after_save(client):
    # Fetch settings again, should return the saved profile
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    
    data = response.json()
    assert "profile_data" in data
    assert data["profile_data"]["instructions"] == "Be very concise and polite."
    assert data["profile_data"]["tone"] == "professional"
