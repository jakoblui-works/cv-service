from aioboto3 import Session

from app.core.config import settings


async def upload_pdf(key: str, pdf: bytes) -> None:
    session = Session()
    async with session.client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        region_name=settings.s3.region,
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key.get_secret_value(),
    ) as s3:
        await s3.put_object(
            Bucket=settings.s3.bucket,
            Key=key,
            Body=pdf,
            ContentType="application/pdf",
        )
