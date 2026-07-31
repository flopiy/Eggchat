class ReplicationManager:

    def __init__(self, graph, replication_factor=3):
        self.graph = graph
        self.replication_factor = replication_factor

    def needs_replication(self, block_id):

        nodes = self.graph.get_nodes(block_id)

        return len(nodes) < self.replication_factor

    def missing_replicas(self, block_id):

        nodes = self.graph.get_nodes(block_id)

        return max(
            0,
            self.replication_factor - len(nodes)
        )

    def check(self):

        result = []

        for block_id in self.graph.blocks:

            if self.needs_replication(block_id):

                result.append({
                    "block": block_id,
                    "missing": self.missing_replicas(block_id)
                })

        return result