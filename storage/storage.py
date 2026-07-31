import hashlib
import json
import os
import shutil

from .metadata import Metadata


class Storage:

    def __init__(self, root="data"):

        self.root = root

        self.blocks_dir = os.path.join(root, "blocks")
        self.files_dir = os.path.join(root, "files")

        os.makedirs(self.blocks_dir, exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)

    def save_file(self, filepath):

        filename = os.path.basename(filepath)

        destination = os.path.join(
            self.files_dir,
            filename
        )

        shutil.copy(filepath, destination)

        file_id = self.hash_file(destination)

        metadata = Metadata(
            file_id=file_id,
            filename=filename,
            size=os.path.getsize(destination)
        )

        self.save_metadata(metadata)

        return metadata

    def hash_file(self, filepath):

        sha = hashlib.sha256()

        with open(filepath, "rb") as f:

            while True:

                chunk = f.read(8192)

                if not chunk:
                    break

                sha.update(chunk)

        return sha.hexdigest()

    def save_metadata(self, metadata):

        path = os.path.join(
            self.files_dir,
            metadata.file_id + ".json"
        )

        with open(path, "w") as f:

            json.dump(
                metadata.__dict__,
                f,
                indent=4
            )

    def load_metadata(self, file_id):

        path = os.path.join(
            self.files_dir,
            file_id + ".json"
        )

        if not os.path.exists(path):
            return None

        with open(path) as f:

            data = json.load(f)

        return Metadata(**data)

    def list_files(self):

        files = []

        for file in os.listdir(self.files_dir):

            if file.endswith(".json"):

                files.append(
                    self.load_metadata(
                        file.replace(".json", "")
                    )
                )

        return files