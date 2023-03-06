from asyncio import sleep
from datetime import datetime
from dateutil import tz
from random import random

from apscheduler.triggers.interval import IntervalTrigger
from mario.pipeline.pipeline import Pipeline, Task, Trigger


class GetData(Task):
    """Fetch raw data"""

    async def run(self, data, params):
        for i in range(10):
            await sleep(1 + random() / 2)
            self.logger.debug("Iteration %d", i)

        self.logger.warning("Nothing serious but you should fix this")

        if random() > 0.75:
            self.logger.error("")
            raise ValueError("I decided to fail :P")


class DummyPipeline(Pipeline):
    """This is a very useless pipeline"""

    tasks = [GetData()]

    triggers = [
        Trigger(
            id="daily",
            name="Daily",
            description="Run the pipeline every day",
            aps_trigger=IntervalTrigger(days=1, start_date=datetime(2023, 1, 1, 22, 30, tzinfo=tz.gettz('Europe/Brussels'))),
        )
    ]
