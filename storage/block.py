from dataclasses import dataclass


@dataclass
class Block:
    block_id: str
    file_id: str
    size: int
    path: str