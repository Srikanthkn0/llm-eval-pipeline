from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models import DatasetListResponse, DatasetUploadResponse
from app.services import dataset_service

router = APIRouter()


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets():
    return DatasetListResponse(datasets=dataset_service.list_datasets())


@router.post("/datasets/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = Form(None),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Upload a .csv file with columns: input, expected_output.",
        )

    content_bytes = await file.read()
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 encoded.",
        ) from exc

    dataset_name = name or file.filename.rsplit(".", 1)[0]
    dataset = dataset_service.save_dataset(dataset_name, content)

    return DatasetUploadResponse(
        message=f"Dataset '{dataset.name}' uploaded with {dataset.row_count} rows.",
        dataset=dataset,
    )
