import io
import json
import os
from pathlib import Path, PurePosixPath
from uuid import uuid4

from app.config import settings


class Storage:
    def __init__(self):
        self.config = settings()
        self.root = self.config.data_dir / "objects"
        self.root.mkdir(parents=True, exist_ok=True)
        self.client = None
        if self.config.storage == "minio":
            from minio import Minio
            from minio.error import S3Error
            self.client = Minio(self.config.minio_endpoint, access_key=self.config.minio_access_key,
                                secret_key=self.config.minio_secret_key, secure=self.config.minio_secure)
            if not self.client.bucket_exists(self.config.minio_bucket):
                try:
                    self.client.make_bucket(self.config.minio_bucket)
                except S3Error as exc:
                    if exc.code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                        raise

    def path(self, key: str) -> Path:
        p = PurePosixPath(key)
        if not key or p.is_absolute() or ".." in p.parts or "\\" in key or ":" in key:
            raise ValueError("Invalid storage key")
        dest = (self.root / key).resolve()
        if not dest.is_relative_to(self.root.resolve()):
            raise ValueError("Invalid storage path")
        return dest

    def put(self, key, content: bytes, content_type="application/octet-stream"):
        dest = self.path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + "." + uuid4().hex + ".tmp")
        tmp.write_bytes(content)
        os.replace(tmp, dest)
        if self.client:
            self.client.put_object(self.config.minio_bucket, key, io.BytesIO(content), len(content),
                                   content_type=content_type)
        return key

    def get(self, key):
        path = self.path(key)
        if not path.exists() and self.client:
            response = self.client.get_object(self.config.minio_bucket, key)
            try:
                self.put(key, response.read())
            finally:
                response.close()
                response.release_conn()
        return path.read_bytes()

    def exists(self, key):
        if self.path(key).exists():
            return True
        if self.client:
            from minio.error import S3Error
            try:
                self.client.stat_object(self.config.minio_bucket, key)
                return True
            except S3Error as exc:
                if exc.code not in {"NoSuchKey", "NoSuchObject"}:
                    raise
        return False

    def put_json(self, key, value):
        return self.put(key, json.dumps(value, ensure_ascii=False, indent=2).encode(), "application/json")

    def get_json(self, key):
        return json.loads(self.get(key))
