---
icon: material/google
status: new
---

Google authentication is supported out-of-the-box, this is the configuration needed
in `plombery.config.yaml`:

```yaml title="plombery.config.yaml"
auth:
  provider: google
  client_id: $GOOGLE_CLIENT_ID
  client_secret: $GOOGLE_CLIENT_SECRET
```

The values starting with `$` are replaced with environmental variables, in this way secret values
are decoupled from the configuration file that is normally versioned in git,
you can modify the name of those variables as long as they match the names used in the `plombery.config.yaml`:

```env title=".env"
GOOGLE_TENANT_ID=""
GOOGLE_CLIENT_ID=""
```
