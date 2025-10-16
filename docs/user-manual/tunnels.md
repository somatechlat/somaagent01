---
title: Secure Tunnel Access
slug: user-tunnels
version: 1.0.0
last-reviewed: 2025-10-15
audience: operators, support
owner: platform-operations
reviewers:
  - platform-engineering
  - security
prerequisites:
  - Working SomaAgent01 deployment with UI authentication enabled
  - Network egress permitted for Cloudflare/Flaredantic endpoints
verification:
  - Tunnel URL issues over HTTPS and terminates when disabled
  - Authentication challenge prompts remote users before granting access
---

# Secure Tunnel Access

SomaAgent01 can expose a local instance to collaborators through the built-in Flaredantic tunnel integration. Use this guide to enable secure sharing, add authentication, and monitor sessions.

## 1. How Tunnels Work

- Backed by the [Flaredantic](https://pypi.org/project/flaredantic/) library.
- Generates a unique HTTPS endpoint per session; no port forwarding required.
- Stops automatically when the UI terminates or you click **Stop Tunnel**.

## 2. Create a Tunnel

1. Open **Settings → External Services**.
2. Select **Flare Tunnel**.
3. Click **Create Tunnel**.
4. Copy the generated URL and share it with stakeholders.
5. Monitor the status badge; green indicates the tunnel is live.

**Verification:** Open the tunnel URL from an external network. The SomaAgent01 login form should appear and the status badge should remain green.

## 3. Secure the Endpoint

Add authentication before sharing:

```bash
export AUTH_LOGIN="viewer"
export AUTH_PASSWORD="strong-secret"
```

Or configure inside the UI:

1. Settings → **External Services** → **Authentication**.
2. Provide UI username and password.
3. Save and restart the session if prompted.

**Security Notes**
- Anyone with the URL can access the UI unless authentication is enforced.
- Tunnels expose only the Agent Zero stack, not the host filesystem, but uploaded files remain accessible within `/work_dir`.
- Rotate tunnel URLs after each engagement.

## 4. Troubleshooting

| Symptom | Resolution |
| ------- | ---------- |
| Tunnel fails to start | Confirm internet access, retry creation, inspect gateway logs |
| URL unreachable | Check corporate firewall/SSL inspection rules |
| Unexpected disconnects | Regenerate the tunnel; ensure the UI process remains running |
| Authentication prompt missing | Verify `AUTH_LOGIN`/`AUTH_PASSWORD` or settings values are set and restart services |

## 5. Close the Tunnel

- Click **Stop Tunnel** in the same settings tab, or
- Shut down the SomaAgent01 UI service; the tunnel terminates automatically.

**Verification:** Accessing the previous tunnel URL should now return an error or timeout within 60 seconds.

## 6. Audit & Compliance

- Log tunnel creation/destruction events in [`docs/changelog.md`](../changelog.md) when used for customer demos or incidents.
- For long-lived tunnels, configure IP allow-lists via Cloudflare Access (roadmap item).

## 7. Related Resources

- [Getting Started](./getting-started.md)
- [Troubleshooting Matrix](./troubleshooting.md)
- [Security Baseline](../technical-manual/security.md)
