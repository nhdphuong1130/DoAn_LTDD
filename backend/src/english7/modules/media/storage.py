from datetime import timedelta
from typing import Protocol


class PresignClient(Protocol):
    def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str: ...

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data,
        length: int,
        content_type: str,
    ): ...

    def get_object(self, bucket_name: str, object_name: str): ...


class MinioStorage:
    def __init__(
        self,
        client: PresignClient,
        *,
        bucket: str,
        expiry_seconds: int,
    ) -> None:
        self._client = client
        self._bucket = bucket
        self._expiry = timedelta(seconds=expiry_seconds)

    def presigned_download(self, object_key: str) -> str:
        return self._client.presigned_get_object(
            self._bucket,
            object_key,
            expires=self._expiry,
        )


class MinioUploadStorage:
    def __init__(self, client: PresignClient, *, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put(self, object_key: str, content: bytes, content_type: str) -> None:
        from io import BytesIO

        self._client.put_object(
            self._bucket,
            object_key,
            BytesIO(content),
            len(content),
            content_type,
        )

    def get(self, object_key: str) -> bytes:
        response = self._client.get_object(self._bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
