from typing import Protocol, Literal, TypedDict, runtime_checkable


class ActionResult(TypedDict, total=False):
    ok: bool
    output: str
    error: str


@runtime_checkable
class Action(Protocol):
    type: Literal["adb", "station"]

    def config_schema(self) -> dict:  # JSON schema for UI
        ...

    async def execute(self, payload: dict) -> ActionResult:
        ...


