---
icon: material/bell
---

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

## `NotificationRule`

A notification rule defines when to send notifications and to whom.

### `pipeline_status`

A list of 1 or more pipeline run status among:

- `completed`
- `failed`
- `cancelled`

### `channels`

A list of 1 or more recipients where to send the notifications.

A channel is an _Apprise_ URI string that defines an email address or a MS Teams
channel, for example:

- **Email** mailto://myuser:mypass@gmail.com
- **MS Teams** msteams://TokenA/TokenB/TokenC/
- **AWS SES** ses://user@domain/AccessKeyID/AccessSecretKey/RegionName/email1/

Behind the scene Plombery uses [Apprise](https://github.com/caronc/apprise),
a library to send notifications to many notification providers, so check their
docs for a full list of the available channels.