import google.oauth2.credentials
import google_auth_oauthlib.flow
from app.core.config import settings

# Gmail scopes required
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

def get_google_auth_flow():
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "project_id": "email-copilot",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
        }
    }
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config, 
        scopes=SCOPES
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow

import json
import os

STATE_FILE = "oauth_state.json"

def get_auth_url():
    flow = get_google_auth_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    state_dict = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state_dict = json.load(f)
        except:
            pass
            
    state_dict[state] = getattr(flow, 'code_verifier', None)
    with open(STATE_FILE, "w") as f:
        json.dump(state_dict, f)
        
    return auth_url, state

def get_credentials_from_code(code: str, state: str = None):
    flow = get_google_auth_flow()
    
    if state and os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state_dict = json.load(f)
            if state in state_dict and state_dict[state]:
                flow.code_verifier = state_dict[state]
        except Exception as e:
            print("Error loading state:", e)

    flow.fetch_token(code=code)
    return flow.credentials
