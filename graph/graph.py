from collections import defaultdict


class Graph:

    def __init__(self):
        # block_id -> set(node_id)
        self.blocks = defaultdict(set)

    def add_block(self, block_id: str, node_id: str):
        self.blocks[block_id].add(node_id)

    def remove_block(self, block_id: str, node_id: str):

        if block_id not in self.blocks:
            return

        self.blocks[block_id].discard(node_id)

        if not self.blocks[block_id]:
            del self.blocks[block_id]

    def get_nodes(self, block_id: str):
        return list(self.blocks.get(block_id, []))

    def has_block(self, block_id: str):
        return block_id in self.blocks

    def block_count(self):
        return len(self.blocks)

    def clear(self):
        self.blocks.clear()

    def to_dict(self):
        return {
            block: list(nodes)
            for block, nodes in self.blocks.items()
        }