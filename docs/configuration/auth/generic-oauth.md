---
icon: material/lock
---

Plombery has a buil-in and ready-to-use authentication system
based on OAuth providers, so you can use your corporate auth system
or Google, Github, etc. as long as they're compatible with OAuth.

To enable the auth system you just need to configure it via the `yml`
config file.

!!! tip "Pre-configured providers"

    This page shows how to configure a generic OAuth provider, though
    some providers are already preconfigured in Plombery from v0.5.0, check
    if your provider is available in the Authentication section of the docs.


!!! info "Good to know"

    The auth system is based on [Authlib](https://authlib.org/)

## `AuthSettings`

Options available

### `provider`

*from v0.5.0*

Can be `microsoft` of `google`, if this field is present, then the client id and secret are required.

If using Microsoft, then you can also use `microsoft_tenant_id`, check the dedicated page.

### `client_id`

An OAuth app client ID

### `client_secret`

An OAuth app client secret

### `microsoft_tenant_id`

The Microsoft tenant ID to be used when using the `provider: microsoft` option.

### `server_metadata_url`

This a special URL that contains information about the OAuth provider
specific endpoints. If your provider doesn't have this URL or you don't
know it, you need to fill up the values for the other URLs: `access_token_url`,
`authorize_url` and `jwks_uri`.

For example, for Google the URL is:

```
https://accounts.google.com/.well-known/openid-configuration
```

### `access_token_url`

### `authorize_url`

### `jwks_uri`

### `client_kwargs`

Additional values to pass to the OAuth client during the auth
process, for example the scope:

```yaml
auth:
  client_kwargs:
    scope: openid email profile
```

### `secret_key`

Secret key used in the backend middleware, this has a dummy default value,
but in production you should define a decent value.
