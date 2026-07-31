from dataclasses import dataclass, field


@dataclass
class Metadata:
    file_id: str
    filename: str
    size: int

    blocks: list[str] = field(default_factory=list)