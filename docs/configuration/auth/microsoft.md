---
icon: material/microsoft
status: new
---

Microsoft authentication is supported out-of-the-box, this is the configuration needed
in `plombery.config.yaml`:

```yaml title="plombery.config.yaml"
auth:
  provider: microsoft
  client_id: $MICROSOFT_CLIENT_ID
  client_secret: $MICROSOFT_CLIENT_SECRET
  microsoft_tenant_id: $MICROSOFT_TENANT_ID
```

The values starting with `$` are replaced with environmental variables, in this way secret values
are decoupled from the configuration file that is normally versioned in git,
you can modify the name of those variables as long as they match the names used in the `plombery.config.yaml`:

```env title=".env"
MICROSOFT_TENANT_ID=""
MICROSOFT_CLIENT_ID=""
MICROSOFT_CLIENT_SECRET=""
```

## Tenant ID

The `microsoft_tenant_id` config is optional and depends on how you registered your application in Azure.

If you configured your Azure Application Registration to allow users only from your tenant, then you need
to supply this option, otherwise this option must be omitted and the `common` tenant is used in the
OAuth endpoints.
