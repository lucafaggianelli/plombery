import httpx

from mario.config import settings


def send(channel: httpx.URL, title: str, data: dict):
    # Create the message payload with actions
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0072C6",
        "summary": title,
        "sections": [
            {
                "activityTitle": title,
                "activityImage": f"{settings.frontend_url}/mario-pipe-flower.png",
                "activityText": f"""Your pipeline {data["pipeline"].name} {data["status_verb"]}""",
                "markdown": True,
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "See pipeline run",
                "targets": [
                    {
                        "os": "default",
                        "uri": data["pipeline_run_url"],
                    }
                ],
            },
        ],
    }

    webhook = str(channel).replace("msteams://", "https://")
    response = httpx.post(webhook, json=message, verify=False)

    # Check the response status code
    response.raise_for_status()
