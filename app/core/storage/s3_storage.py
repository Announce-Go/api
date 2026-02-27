from __future__ import annotations

import uuid
from pathlib import Path
from typing import BinaryIO, Optional

import aioboto3
from botocore.exceptions import ClientError

from app.core.storage.abstract_storage import AbstractStorage
from app.core.timezone import now_kst


class S3Storage(AbstractStorage):
    """AWS S3 저장소"""

    def __init__(self, bucket: str, region: str):
        self._bucket = bucket
        self._region = region
        self._client = None

    async def connect(self) -> None:
        """S3 클라이언트 초기화 및 버킷 접근 검증

        boto3 기본 credential chain을 사용한다.
        (로컬: ~/.aws/credentials 또는 환경변수, ECS: Task Role)
        """
        session = aioboto3.Session(region_name=self._region)
        self._client = await session.client("s3").__aenter__()
        await self._client.head_bucket(Bucket=self._bucket)  # 실제 버킷 접근 검증

    async def disconnect(self) -> None:
        """S3 클라이언트 종료"""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    def _generate_storage_path(self, original_filename: str) -> str:
        """고유한 저장 경로 생성 (YYYY/MM/DD/uuid.ext)"""
        today = now_kst().strftime("%Y/%m/%d")
        ext = Path(original_filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return f"{today}/{unique_name}"

    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        """파일 업로드"""
        storage_path = self._generate_storage_path(filename)
        content = file.read()

        await self._client.put_object(
            Bucket=self._bucket,
            Key=storage_path,
            Body=content,
            ContentType=content_type,
        )

        return storage_path

    async def download(self, storage_path: str) -> Optional[bytes]:
        """파일 다운로드"""
        try:
            response = await self._client.get_object(
                Bucket=self._bucket,
                Key=storage_path,
            )
            return await response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    async def delete(self, storage_path: str) -> bool:
        """파일 삭제"""
        if not await self.exists(storage_path):
            return False

        await self._client.delete_object(
            Bucket=self._bucket,
            Key=storage_path,
        )
        return True

    async def exists(self, storage_path: str) -> bool:
        """파일 존재 여부 확인"""
        try:
            await self._client.head_object(
                Bucket=self._bucket,
                Key=storage_path,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
