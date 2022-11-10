from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AddOperands(_message.Message):
    __slots__ = ["ina", "inb"]
    INA_FIELD_NUMBER: _ClassVar[int]
    INB_FIELD_NUMBER: _ClassVar[int]
    ina: int
    inb: int
    def __init__(self, ina: _Optional[int] = ..., inb: _Optional[int] = ...) -> None: ...

class AddResult(_message.Message):
    __slots__ = ["res"]
    RES_FIELD_NUMBER: _ClassVar[int]
    res: int
    def __init__(self, res: _Optional[int] = ...) -> None: ...
