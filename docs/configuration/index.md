---
icon: material/cog
---

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
