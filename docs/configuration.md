Plombery is configurable via environmental variables, a YAML file
or even better via a combination of the 2.

!!! info "Why a hybrid configuration?"

    An entire configuration can be quite large so storing it as environmental
    variables can be quite hard to maintain, moreover some parts of the
    configuration should be stored together with the code as they are part
    of the system and some parts of it are secret so you need env vars

Create a configuration file in the root of your project named `plombery.config.yaml`
(or `plombery.config.yml` if you prefer) and set the values you need, you should
commit this file to the git repo:

```yaml title="plombery.config.yaml"
frontend_url: https://pipelines.example.com

auth:
  client_id: $GOOGLE_CLIENT_ID
  client_secret: $GOOGLE_CLIENT_SECRET
  server_metadata_url: https://accounts.google.com/.well-known/openid-configuration

notifications:
  - pipeline_status:
      - failed
    channels:
      - $GMAIL_ACCOUNT
      - $MSTEAMS_WEBHOOK
```

Now define the secrets as environmental variables in a `.env` file,
in your shell or in your hosting environment.


!!! tip

    By default, Plombery will load any `.env` found in your project root.

!!! Warning

    You shouldn't commit the `.env` file as it contains secrets!

```shell title=".env"
# Auth
GOOGLE_CLIENT_ID="ABC123"
GOOGLE_CLIENT_SECRET="DEF456"

# Notifications
GMAIL_ACCOUNT=mailto://myuser:mypass@gmail.com
MSTEAMS_WEBHOOK=msteams://TokenA/TokenB/TokenC/
```

## System

!!! tip

    If you're running Plombery locally, in most cases you don't need to change
    these settings

### `database_url`

The Sqlite DB URI, by default `sqlite:///./plombery.db`

### `allowed_origins`

It allows to configure the CORS header `Access-Control-Allow-Origin`,
by default it's value is `*` so it allows all origins.

**Change it if running in production.**

### `frontend_url`

The URL of the frontend, by default is the same as the backend,
change it if the frontend is served at a different URL, for example
during the frontend development.

## Notifications

Plombery can send notifications after a pipeline has run based on the status
of the run itself (success, failure, etc.).

The notifications configuration can be defined in the YAML
file as a list of [`NotificationRule`](#notificationrule)s:

```yaml title="plombery.config.yaml"
notifications:
  # Send notifications only if the pipelines failed
  - pipeline_status:
      - failed
    channels:
      # Send them to my gmail address (from my address itself)
      # Better to use an env var here
      - mailto://myuser:mypass@gmail.com
  # Send notifications only if the pipelines succeeded or was cancelled
  - pipeline_status:
      - completed
      - cancelled
    channels:
      # Send them to a MS Teams channel
      # Better to use an env var here
      - msteams://mychanneltoken
```

### `NotificationRule`

A notification rule defines when to send notifications and to whom.

#### `pipeline_status`

A list of 1 or more pipeline run status among:

  * `completed`
  * `failed`
  * `cancelled`

#### `channels`

A list of 1 or more recipients where to send the notifications.

A channel is an *Apprise* URI string that defines an email address or a MS Teams
channel, for example:

* **Email** mailto://myuser:mypass@gmail.com
* **MS Teams** msteams://TokenA/TokenB/TokenC/
* **AWS SES** ses://user@domain/AccessKeyID/AccessSecretKey/RegionName/email1/

Behind the scene Plombery uses [Apprise](https://github.com/caronc/apprise),
a library to send notifications to many notification providers, so check their
docs for a full list of the available channels.

## Authentication

Plombery has a buil-in and ready-to-use authentication system
based on OAuth providers, so you can use your corporate auth system
or Google, Github, etc.

To enable the auth system you just need to configure it.

!!! info "Good to know"

    The auth system is based on [Authlib](https://authlib.org/)

### `AuthSettings`

Options available

#### `client_id`

An OAuth app client ID

#### `client_secret`

An OAuth app client secret

#### `server_metadata_url`

This a special URL that contains information about the OAuth provider
specific endpoints. If your provider doesn't have this URL or you don't
know it, you need to fill up the values for the other URLs: `access_token_url`,
`authorize_url` and `jwks_uri`.

Here a table of well known Metadata URLs:

| Provider | URL |
| -------- | --- |
| Google | https://accounts.google.com/.well-known/openid-configuration |

#### `access_token_url`

#### `authorize_url`

#### `jwks_uri`

#### `client_kwargs`

Additional values to pass to the OAuth client during the auth
process, for example the scope:

```yaml
auth:
  client_kwargs:
    scope: openid email profile
```

#### `secret_key`

Secret key used in the backend middleware, this has a dummy default value,
but in production you should define a decent value.
