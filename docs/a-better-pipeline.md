

```py
register_pipeline(
    id="sales_pipeline",
    description="""This is a very useless pipeline""",
    tasks=[get_sales_data],
    triggers=[
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            params=InputParams(some_value=2),
            aps_trigger=IntervalTrigger(
                days=1,
                start_date=datetime(
                    2023, 1, 1, 22, 30, tzinfo=tz.gettz("Europe/Brussels")
                ),
            ),
        )
    ],
    params=InputParams,
)
```