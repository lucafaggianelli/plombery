import asyncio
from typing import Any, Callable, Coroutine


EventPayload = Any
EventSelector = tuple
Listener = Callable | Coroutine
ListenersRegistry = dict[EventSelector, set[Listener]]


class Bus:
    listeners: ListenersRegistry = {}
    once_listeners: ListenersRegistry = {}

    def _register_listener(
        self, event_name: EventSelector, listener: Listener, registry: ListenersRegistry
    ):
        if event_name not in registry:
            registry[event_name] = set()

        registry[event_name].add(listener)

    def _remove_listener(
        self, event_name: EventSelector, listener: Listener, registry: ListenersRegistry
    ):
        if event_name in registry:
            registry[event_name].remove(listener)

    def on(self, event_name: EventSelector, listener: Listener):
        self._register_listener(event_name, listener, self.listeners)

    def once(self, event_name: EventSelector, listener: Listener):
        self._register_listener(event_name, listener, self.once_listeners)

    def off(self, event_name: EventSelector, listener: Listener | None = None):
        if listener:
            self._remove_listener(event_name, listener, self.listeners)
            self._remove_listener(event_name, listener, self.once_listeners)
        else:
            # Remove all listeners for an event
            self.listeners.pop(event_name, None)
            self.once_listeners.pop(event_name, None)

    def _call_listeners(self, listeners: set[Listener], payload: EventPayload):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        tasks = set()

        for listener in listeners:
            if asyncio.iscoroutinefunction(listener):
                task = loop.create_task(listener())
            else:
                task = loop.run_in_executor(None, listener, payload)

            tasks.add(task)
            task.add_done_callback(tasks.discard)

    def emit(self, event_name: EventSelector, payload: Any | None = None):
        listeners = self.listeners.get(event_name, set()).union(
            self.once_listeners.pop(event_name, set())
        )

        self._call_listeners(listeners, payload)


bus = Bus()


async def wait_for_run_completion(run_id: int):
    run_completion_event = asyncio.Event()

    async def on_job_completed():
        run_completion_event.set()

    bus.once(("run", run_id, "completed"), on_job_completed)

    await run_completion_event.wait()


if __name__ == "__main__":

    async def main():
        event = asyncio.Event()

        async def on():
            print("Enter")
            await asyncio.sleep(2)
            event.set()
            print("Done")

        bus.on(("run", 12, "completed"), lambda *args: print("Hey got it"))
        bus.on(("run", 12, "completed"), on)

        bus.emit(("run", 12, "completed"))
        print("called emit")

        await event.wait()

    asyncio.new_event_loop().run_until_complete(main())
