import boto3
from botocore.config import Config

from src.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def download_object(object_key: str, destination_path: str) -> None:
    client = get_s3_client()
    with open(destination_path, "wb") as handle:
        client.download_fileobj(settings.s3_bucket, object_key, handle)


def upload_object(source_path: str, object_key: str, content_type: str) -> None:
    client = get_s3_client()
    with open(source_path, "rb") as handle:
        client.upload_fileobj(
            handle,
            settings.s3_bucket,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )


def create_presigned_get_url(object_key: str, expires_in: int, use_public_endpoint: bool = True) -> str:
    # Por defecto usa endpoint público para AssemblyAI (necesita acceso desde internet)
    # use_public_endpoint=False para uso local
    endpoint_url = settings.s3_public_endpoint if use_public_endpoint and settings.s3_public_endpoint else settings.s3_endpoint
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    params = {"Bucket": settings.s3_bucket, "Key": object_key}
    return client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
    )