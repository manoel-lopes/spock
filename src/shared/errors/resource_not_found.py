from typing import Literal

Resource = Literal["User", "Token", "Fund", "Report", "Job", "TransparencyScore"]


class ResourceNotFoundError(Exception):
    def __init__(self, resource: Resource) -> None:
        super().__init__(f"{resource} not found")
        self.resource = resource
