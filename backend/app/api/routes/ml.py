from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.case import Case
from app.models.enums import MlTaskName
from app.models.ml_model import MlModel
from app.schemas.evaluation import CalibrationRecordRead
from app.schemas.ml import (
    CasePredictionRead,
    CaseTypeTextPredictionRead,
    CaseTypeTextPredictRequest,
    LegalIssueModelHealthRead,
    LegalIssuePredictionRead,
    LegalIssuePredictionRequest,
    MlDatasetBuildRequest,
    MlDatasetRead,
    MlRuntimeHealthRead,
    MlModelDiagnosticsRead,
    MlModelRead,
    MlPredictRequest,
    MlTaskLeaderboardRead,
    MlTrainRequest,
    PredictionExplanationRead,
)
from app.services.evaluation.calibration import build_calibration_record, get_calibration_record
from app.services.ml.datasets.builder import build_ml_datasets
from app.services.ml.training.diagnostics import explain_case_predictions, get_model_diagnostics
from app.services.ml.training.inference import (
    get_case_for_prediction,
    get_latest_model_for_task,
    get_model_or_none,
    list_case_predictions,
    predict_case_tasks,
)
from app.services.ml.training.imported_case_type import (
    ensure_imported_case_type_model_record,
    get_case_type_model_health,
    predict_case_type_text,
)
from app.services.ml.training.imported_legal_issue import (
    ensure_imported_legal_issue_model_record,
    get_legal_issue_model_health,
    predict_legal_issues,
)
from app.services.ml.training.trainer import (
    get_dataset_or_none,
    get_ml_model_or_none,
    list_ml_datasets,
    list_ml_models,
    train_ml_model,
)
from app.services.serializers import (
    serialize_case_prediction,
    serialize_ml_dataset,
    serialize_ml_leaderboard,
    serialize_ml_model,
)
from app.utils.http import not_found

router = APIRouter()


@router.get("/ml/health", response_model=MlRuntimeHealthRead)
def get_ml_runtime_health() -> MlRuntimeHealthRead:
    return MlRuntimeHealthRead(**get_case_type_model_health())


@router.get("/ml/models/case-type/health", response_model=MlRuntimeHealthRead)
def get_case_type_model_runtime_health() -> MlRuntimeHealthRead:
    return MlRuntimeHealthRead(**get_case_type_model_health())


@router.get("/ml/models/legal-issues/health", response_model=LegalIssueModelHealthRead)
def get_legal_issue_model_runtime_health() -> LegalIssueModelHealthRead:
    return LegalIssueModelHealthRead(**get_legal_issue_model_health())


@router.post("/ml/datasets/build", response_model=list[MlDatasetRead], status_code=status.HTTP_201_CREATED)
def build_datasets(
    payload: MlDatasetBuildRequest,
    db: Session = Depends(get_db),
) -> list[MlDatasetRead]:
    datasets = build_ml_datasets(db, task_name=payload.task_name)
    return [serialize_ml_dataset(dataset) for dataset in datasets]


@router.get("/ml/datasets", response_model=list[MlDatasetRead])
def get_datasets(db: Session = Depends(get_db)) -> list[MlDatasetRead]:
    return [serialize_ml_dataset(dataset) for dataset in list_ml_datasets(db)]


@router.get("/ml/datasets/{dataset_id}", response_model=MlDatasetRead)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> MlDatasetRead:
    dataset = get_dataset_or_none(db, dataset_id)
    if not dataset:
        raise not_found("Dataset not found.")
    return serialize_ml_dataset(dataset)


@router.post("/ml/train", response_model=MlModelRead, status_code=status.HTTP_201_CREATED)
def train_model(
    payload: MlTrainRequest,
    db: Session = Depends(get_db),
) -> MlModelRead:
    dataset = get_dataset_or_none(db, payload.dataset_id)
    if not dataset:
        raise not_found("Dataset not found.")
    model = train_ml_model(
        db,
        dataset=dataset,
        model_family=payload.model_family,
        model_name=payload.model_name,
        hyperparameters=payload.hyperparameters,
    )
    return serialize_ml_model(model)


@router.get("/ml/models", response_model=list[MlModelRead])
def get_models(db: Session = Depends(get_db)) -> list[MlModelRead]:
    ensure_imported_case_type_model_record(db)
    ensure_imported_legal_issue_model_record(db)
    return [serialize_ml_model(model) for model in list_ml_models(db)]


@router.get("/ml/models/{model_id}", response_model=MlModelRead)
def get_model(model_id: str, db: Session = Depends(get_db)) -> MlModelRead:
    model = get_ml_model_or_none(db, model_id)
    if not model:
        raise not_found("Model not found.")
    return serialize_ml_model(model)


@router.get("/ml/models/{model_id}/metrics", response_model=dict)
def get_model_metrics(model_id: str, db: Session = Depends(get_db)) -> dict:
    model = get_ml_model_or_none(db, model_id)
    if not model:
        raise not_found("Model not found.")
    return model.metrics_json


@router.get("/ml/models/{model_id}/diagnostics", response_model=MlModelDiagnosticsRead)
def get_model_diagnostic_details(model_id: str, db: Session = Depends(get_db)) -> MlModelDiagnosticsRead:
    model = get_ml_model_or_none(db, model_id)
    if not model:
        raise not_found("Model not found.")
    return MlModelDiagnosticsRead(
        model_id=model.id,
        task_name=model.task_name,
        model_family=model.model_family,
        model_name=model.name,
        diagnostics=get_model_diagnostics(model),
    )


@router.get("/ml/models/{model_id}/calibration", response_model=CalibrationRecordRead)
def get_model_calibration(model_id: str, db: Session = Depends(get_db)) -> CalibrationRecordRead:
    model = get_ml_model_or_none(db, model_id)
    if not model:
        raise not_found("Model not found.")
    record = get_calibration_record(model_id) or build_calibration_record(db, model=model, persist=False)
    return CalibrationRecordRead(**record)


@router.post("/ml/models/{model_id}/calibration/build", response_model=CalibrationRecordRead, status_code=status.HTTP_201_CREATED)
def build_model_calibration(model_id: str, db: Session = Depends(get_db)) -> CalibrationRecordRead:
    model = get_ml_model_or_none(db, model_id)
    if not model:
        raise not_found("Model not found.")
    return CalibrationRecordRead(**build_calibration_record(db, model=model, persist=True))


@router.get("/ml/tasks/{task_name}/leaderboard", response_model=MlTaskLeaderboardRead)
def get_leaderboard(task_name: MlTaskName, db: Session = Depends(get_db)) -> MlTaskLeaderboardRead:
    if task_name == MlTaskName.CASE_TYPE:
        ensure_imported_case_type_model_record(db)
    elif task_name == MlTaskName.LEGAL_ISSUE_CLASSIFIER:
        ensure_imported_legal_issue_model_record(db)
    models = list(
        db.scalars(
            select(MlModel)
            .where(MlModel.task_name == task_name)
            .order_by(MlModel.created_at.desc())
        ).all()
    )
    models = sorted(models, key=lambda model: float(model.metrics_json.get("primaryMetric", 0.0)), reverse=True)
    return serialize_ml_leaderboard(task_name, models)


@router.post("/ml/predict", response_model=list[CasePredictionRead], status_code=status.HTTP_201_CREATED)
def predict_for_case(
    payload: MlPredictRequest,
    db: Session = Depends(get_db),
) -> list[CasePredictionRead]:
    case = get_case_for_prediction(db, payload.case_id)
    if not case:
        raise not_found("Case not found.")
    predictions = predict_case_tasks(
        db,
        case=case,
        task_name=payload.task_name,
        model_id=payload.model_id,
    )
    return [serialize_case_prediction(prediction) for prediction in predictions]


@router.post("/ml/predict/case-type", response_model=CaseTypeTextPredictionRead)
def predict_case_type_from_text(payload: CaseTypeTextPredictRequest) -> CaseTypeTextPredictionRead:
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Text is required.")

    result = predict_case_type_text(payload.text)
    if not payload.include_probabilities:
        result["probabilities"] = {}
    if payload.include_metadata:
        result["metadata"] = {
            "modelSource": result.get("model_source"),
            "modelStatus": result.get("model_status"),
            "modelName": result.get("model_name"),
            "bundleManifest": result.get("bundle_manifest", {}),
            "metrics": result.get("metrics", {}),
        }
    else:
        result["bundle_manifest"] = {}
        result["metrics"] = {}
        result["metadata"] = {}
    return CaseTypeTextPredictionRead(**result)


@router.post("/ml/predict/legal-issues", response_model=LegalIssuePredictionRead)
def predict_legal_issues_from_text(payload: LegalIssuePredictionRequest) -> LegalIssuePredictionRead:
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Text is required.")

    result = predict_legal_issues(
        payload.text,
        threshold=payload.threshold,
        top_k=payload.top_k,
        include_probabilities=payload.include_probabilities,
        include_metadata=payload.include_metadata,
    )
    return LegalIssuePredictionRead(**result)


@router.post("/cases/{case_id}/predict", response_model=list[CasePredictionRead], status_code=status.HTTP_201_CREATED)
def predict_case_route(
    case_id: str,
    payload: MlPredictRequest,
    db: Session = Depends(get_db),
) -> list[CasePredictionRead]:
    case = get_case_for_prediction(db, case_id)
    if not case:
        raise not_found("Case not found.")
    predictions = predict_case_tasks(
        db,
        case=case,
        task_name=payload.task_name,
        model_id=payload.model_id,
    )
    return [serialize_case_prediction(prediction) for prediction in predictions]


@router.get("/cases/{case_id}/predictions", response_model=list[CasePredictionRead])
def get_case_predictions(case_id: str, db: Session = Depends(get_db)) -> list[CasePredictionRead]:
    case = get_case_for_prediction(db, case_id)
    if not case:
        raise not_found("Case not found.")
    return [serialize_case_prediction(prediction) for prediction in list_case_predictions(db, case_id)]


@router.get("/cases/{case_id}/predictions/explain", response_model=list[PredictionExplanationRead])
def get_case_prediction_explanations(case_id: str, db: Session = Depends(get_db)) -> list[PredictionExplanationRead]:
    case = get_case_for_prediction(db, case_id)
    if not case:
        raise not_found("Case not found.")
    return [PredictionExplanationRead(**item) for item in explain_case_predictions(db, case_id)]
