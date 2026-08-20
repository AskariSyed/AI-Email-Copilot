# Security Review & Architecture
**AI Email Copilot**

This document outlines the security posture, threat models, and protective implementations of the AI Email Copilot repository. It serves as a reference for understanding both the strengths and the current MVP limitations of the system.

## 1. Security Architecture
The application is a decoupled system (Vite/React frontend, FastAPI backend, PostgreSQL database) that processes highly sensitive personal data (emails). The security architecture focuses heavily on mitigating threats from the unverified external data (the emails themselves) via strict sanitization, sandboxing, and prompt isolation.

## 2. Threat Model
**Primary Assets:**
- Google OAuth Access & Refresh Tokens.
- Raw historical email content (PII).
- The user's AI Style Profile.

**Primary Threats:**
- **Prompt Injection**: Malicious instructions embedded in incoming emails altering LLM behavior.
- **Cross-Site Scripting (XSS)**: Malicious HTML/JS embedded in incoming emails executing in the user's browser.
- **Unauthorized API Access**: External actors querying the backend to read private emails.
- **Database Exfiltration**: Attackers stealing stored OAuth tokens to hijack Gmail accounts.

## 3. Authentication
- **Current State**: The backend API endpoints currently lack session or token-based authentication (like JWT). For MVP simplicity, the `user_id = 1` is hardcoded across the backend.
- **Vulnerability**: Any client that can reach the `localhost:8000` port can access all emails and trigger actions.
- **Mitigation**: See section 14 (Recommended Production Hardening).

## 4. Authorization
- **Current State**: The system relies on the assumption of a single-tenant local deployment. There are no Role-Based Access Controls (RBAC) or tenant isolations implemented beyond querying by the hardcoded `user_id`.

## 5. OAuth Security
- **Implementation**: The backend uses the official `google-auth-oauthlib` and standard OAuth2 callback flow.
- **Gmail API Scopes**: The system requests broad Gmail scopes to read, draft, and send emails on the user's behalf.
- **Vulnerability**: Access and Refresh tokens are stored in plain text within the `gmail_accounts` PostgreSQL table.

## 6. Email Data Privacy
- **Vector Database**: Raw email chunks and their embeddings are stored indefinitely in the database.
- **LLM Privacy**: Private email data is sent to external APIs (OpenAI / Groq) for processing. Ensure enterprise data agreements are in place if deploying to production.

## 7. HTML/XSS Protection
The system employs a highly effective two-tiered defense against XSS:
- **Backend Sanitization**: `services/gmail/sync.py` uses `BeautifulSoup` to aggressively extract and destroy all `<script>` and `<style>` tags before text is embedded into the vector database.
- **Frontend Sandboxing**: `App.tsx` renders raw HTML emails using an `iframe` with the `srcDoc` attribute. The `sandbox` attribute is strictly set to `"allow-popups allow-popups-to-escape-sandbox allow-same-origin"`. Because `allow-scripts` is intentionally omitted, Javascript execution is entirely blocked at the browser level, rendering XSS attacks inert.

## 8. Prompt Injection Defenses
Because the LLM processes unverified external data (emails), strict prompt injection defenses are implemented:
- **Structural Isolation**: Untrusted context (incoming emails, historical threads) is completely decoupled from the System Prompt and moved to the User Prompt.
- **XML Delimiters**: All untrusted data is wrapped in strict tags (e.g., `<untrusted_incoming_email>`).
- **Override Directives**: Explicit instructions immediately precede the XML tags, commanding the LLM to treat the blocks as passive data.
- **Output Validation**: Basic string matching aborts the generation if the LLM leaks classic injection signatures (e.g., *"You are an AI..."*).
- **Human-in-the-Loop**: The LLM is structurally isolated from executing actions (like sending an email). It only generates drafts, requiring explicit human approval to fire the Gmail API.

## 9. Secret Management
- **Environment Variables**: API keys (OpenAI, Groq, Google Client Secret, Postgres URI) are loaded securely via `.env` files using `pydantic-settings`.
- **Exclusion**: The `.env` file is properly listed in `.gitignore`.

## 10. Database Security
- **SQL Injection**: The application exclusively uses SQLAlchemy ORM, which inherently parameterizes queries, virtually eliminating SQL injection risks.

## 11. API Security
- **CORS**: Configured strictly in `main.py` via `CORSMiddleware`, exclusively allowing requests from `http://localhost:5173`.
- **Rate Limiting**: Currently not implemented. The API is vulnerable to local DoS or spamming of LLM endpoints.

## 12. Logging / Privacy Considerations
- **LLM Logging**: Raw prompts containing PII are not actively dumped to `logging.info`, minimizing leakage into system logs.
- **Vector Latency**: Only metadata and latency metrics are logged during retrieval.

## 13. Known Limitations (MVP)
The following are accepted risks for the current local MVP, but are critical vulnerabilities for any public deployment:
1. Lack of API Authentication (JWT/Sessions).
2. Plain text storage of OAuth tokens in the database.
3. Lack of database encryption at rest.

## 14. Recommended Production Hardening
Before deploying this application to a public server, the following **MUST** be implemented:
1. **API Authentication**: Implement OAuth2 with JWT Bearer tokens to protect all FastAPI routes. Extract `user_id` from the JWT rather than hardcoding.
2. **Token Encryption**: Encrypt `access_token` and `refresh_token` in the database using AES-GCM (e.g., via `cryptography.fernet`) and a secure symmetric key injected via environment variables.
3. **Data Retention**: Implement background workers to prune old emails and embeddings to minimize the impact of a data breach.
4. **Rate Limiting**: Use a library like `slowapi` to prevent abuse of the expensive LLM endpoints.
