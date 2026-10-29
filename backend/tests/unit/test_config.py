from app.core.config import Settings


def test_settings_load_defaults():
    s = Settings(
        DB_HOST="127.0.0.1",
        DB_PORT=3306,
        DB_NAME="mule_matrix",
        DB_USER="root",
        DB_PASSWORD="test_password",
    )
    assert s.DB_HOST == "127.0.0.1"
    assert s.DB_NAME == "mule_matrix"
    assert "test_password" in s.database_url
    assert "***" in s.sanitized_database_url
    assert "test_password" not in s.sanitized_database_url


def test_cors_origins_parsing():
    s = Settings(CORS_ORIGINS="http://localhost:5173, http://127.0.0.1:5173")
    origins = s.cors_origin_list
    assert len(origins) == 2
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins

