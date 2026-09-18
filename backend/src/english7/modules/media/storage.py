from datetime import timedelta
from typing import Protocol


class PresignClient(Protocol):
    def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str: ...


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

