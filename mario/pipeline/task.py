from pydantic import BaseModel

from ._utils import to_snake_case


class Task:
    params: BaseModel = None
    uuid: str = None
    description: str = __doc__

    def __init__(self):
        self.uuid = to_snake_case(self.__class__.__name__)

    def run(self, *args, params: BaseModel = None, **kwargs):
        pass

    def tests(self, *args, params: BaseModel = None, **kwargs):
        pass
