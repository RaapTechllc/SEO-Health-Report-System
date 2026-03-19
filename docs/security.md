# Security Documentation

## SSRF Protection

`safe_fetch.py` prevents Server-Side Request Forgery attacks by validating all outbound requests.

### Blocked IP Ranges

**IPv4:**
- `127.0.0.0/8` - Loopback
- `10.0.0.0/8` - Private (Class A)
- `172.16.0.0/12` - Private (Class B)
- `192.168.0.0/16` - Private (Class C)
- `169.254.0.0/16` - Link-local

**IPv6:**
- `::1/128` - Loopback
- `fc00::/7` - Unique local
- `fe80::/10` - Link-local

### Additional Protections

- **Redirect attacks**: Redirects to private IPs are blocked
- **Scheme validation**: Only `http://` and `https://` allowed
- **Credential rejection**: URLs containing userinfo (user:pass@) are rejected

## Redaction

`redaction.py` strips sensitive data from logs and stored responses.

### Redacted Patterns

- API keys (`api_key`, `apikey`, `api-key`)
- Tokens (`token`, `access_token`, `bearer`)
- Secrets (`secret`, `client_secret`)
- Passwords (`password`, `passwd`)
- Auth headers (`Authorization`, `X-Api-Key`)
- Cookies (`Set-Cookie`, `Cookie`)

Redacted values appear as `[REDACTED]` in logs and storage.

## Webhook Security

### HMAC-SHA256 Signing

All webhook payloads are signed using HMAC-SHA256:

```
X-Webhook-Signature: sha256=<hex-encoded-signature>
```

Receivers should:
1. Extract the signature from the header
2. Compute HMAC-SHA256 of the raw request body using the shared secret
3. Compare signatures using constant-time comparison

### Callback URL Validation

Webhook callback URLs pass through SSRF validation before any request is made, preventing attackers from targeting internal services.
