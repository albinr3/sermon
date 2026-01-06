import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

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


def ensure_bucket_exists() -> None:
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code not in {"404", "NoSuchBucket"}:
            raise
        client.create_bucket(Bucket=settings.s3_bucket)


def create_presigned_put_url(
    object_name: str, content_type: str | None, expires_in: int
) -> str:
    endpoint_url = settings.s3_public_endpoint or settings.s3_endpoint
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    params = {"Bucket": settings.s3_bucket, "Key": object_name}
    if content_type:
        params["ContentType"] = content_type

    return client.generate_presigned_url(
        "put_object",
        Params=params,
        ExpiresIn=expires_in,
    )


def create_presigned_get_url(object_name: str, expires_in: int) -> str:
    endpoint_url = settings.s3_public_endpoint or settings.s3_endpoint
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    params = {"Bucket": settings.s3_bucket, "Key": object_name}
    return client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
    )
