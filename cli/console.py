class Console:
    def __init__(self, node):
        self.node = node
        self.running = False
        self.chat_mode = False

    def run(self):
        self.running = True
        print("\nCommands:")
        print("  connect <host> <port>     - connect to remote node")
        print("  find <node_id>            - find and connect by NodeID")
        print("  auto                      - auto-find all nodes from rendezvous")
        print("  chat                      - enter continuous chat mode")
        print("  send <text>               - send a single message")
        print("  put <filepath>            - send a file to all peers")
        print("  peers                     - list connected peers")
        print("  /rendezvous <host> <port> - register on rendezvous coordinator")
        print("  /stats                    - show LLG compression statistics")
        print("  /llg                      - show first 10 words in LLG")
        print("  /dialogues                - show dialogue hashes")
        print("  exit                      - stop the node")
        print("")

        while self.running:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue

                if self.chat_mode:
                    if cmd.startswith("/"):
                        self._handle_chat_command(cmd[1:].strip())
                    else:
                        self.node.send_message(cmd)
                else:
                    self._handle_command(cmd)

            except KeyboardInterrupt:
                if self.chat_mode:
                    print("\nExiting chat mode...")
                    self.chat_mode = False
                else:
                    self._handle_command("exit")
            except Exception as e:
                print(f"Error: {e}")

    def _handle_command(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return

        command = parts[0].lower()

        if command == "exit":
            self.running = False
            self.node.stop()

        elif command == "connect" and len(parts) == 3:
            host = parts[1]
            port = int(parts[2])
            self.node.connect(host, port)

        elif command == "find" and len(parts) == 2:
            target = parts[1]
            self.node.find_node(target)

        elif command == "auto":
            self.node.auto_find_all()

        elif command == "send" and len(parts) >= 2:
            text = " ".join(parts[1:])
            self.node.send_message(text)

        elif command == "put" and len(parts) == 2:
            filepath = parts[1]
            self.node.send_file(filepath)

        elif command == "chat":
            if not self.node.peers:
                print("No active connections. Connect to a peer first.")
            else:
                self.chat_mode = True
                print("\n=== Chat mode ===")
                print("Type your messages. Commands:")
                print("  /peers       - list connected peers")
                print("  /find <id>   - find node by ID")
                print("  /auto        - auto-find all nodes")
                print("  /send <text> - send a message explicitly")
                print("  /put <file>  - send a file")
                print("  /stats       - show LLG stats")
                print("  /llg         - show LLG sample")
                print("  /dialogues   - show dialogue hashes")
                print("  /exit        - leave chat mode")
                print("  /quit        - stop the node")
                print("")

        elif command == "peers":
            self._print_peers()

        elif command == "/rendezvous" and len(parts) == 3:
            host = parts[1]
            port = int(parts[2])
            self.node.rendezvous_register(host, port)

        elif command == "/stats":
            self._print_stats()

        elif command == "/llg":
            self._print_llg_sample()

        elif command == "/dialogues":
            self._print_dialogues()

        else:
            print(f"Unknown command: {cmd}")

    def _handle_chat_command(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return

        command = parts[0].lower()

        if command == "exit":
            self.chat_mode = False
            print("Exited chat mode.")
        elif command == "quit":
            self.running = False
            self.node.stop()
        elif command == "peers":
            self._print_peers()
        elif command == "find" and len(parts) == 2:
            self.node.find_node(parts[1])
        elif command == "auto":
            self.node.auto_find_all()
        elif command == "send" and len(parts) >= 2:
            text = " ".join(parts[1:])
            self.node.send_message(text)
        elif command == "put" and len(parts) == 2:
            self.node.send_file(parts[1])
        elif command == "stats":
            self._print_stats()
        elif command == "llg":
            self._print_llg_sample()
        elif command == "dialogues":
            self._print_dialogues()
        else:
            print(f"Unknown chat command: /{cmd}")

    def _print_peers(self):
        peers = self.node.list_peers()
        if peers:
            print("Connected peers:")
            for name, addr in peers:
                print(f"  {name} @ {addr[0]}:{addr[1]}")
        else:
            print("No peers")

    def _print_stats(self):
        stats = self.node.get_stats()
        print("\n=== LLG Statistics ===")
        print(f"  Unique words in graph: {stats['unique_words']}")
        print(f"  Total words processed: {stats['total_words_processed']}")
        print(f"  Estimated savings: {stats['estimated_savings']}")
        print("======================")

    def _print_llg_sample(self):
        sample = self.node.get_llg_sample()
        print("\n=== LLG Sample (first 10 words) ===")
        for word, wid in sample.items():
            print(f"  {word} -> ID {wid}")
        print(f"  Total unique words: {self.node.llg.size}")
        print("=====================================")

    def _print_dialogues(self):
        dialogues = self.node.get_dialogue_hashes()
        if not dialogues:
            print("No dialogues recorded.")
            return
        print("\n=== Dialogue Hashes ===")
        for peer_id, dh in dialogues.items():
            print(f"  Peer: {peer_id.hex()[:8]}")
            print(f"    Block hash: {dh['block_hash']}")
            print(f"    Block size: {dh['block_size']} bytes")
            print(f"    Word count: {dh['word_count']}")
            print(f"    Message count: {dh['message_count']}")
        print("========================")