from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from backend.analytics import analyze_dataset, calculate_kpis
from backend.cleaning import clean_file
from backend.profiling import profile_csv
from backend.anomaly import detect_anomalies
from pydantic import BaseModel

from backend.auth import (
    register_user,
    login_user,
    get_current_user,
    require_role
)

from backend.database import (
    insert_dataset,
    insert_quality_report,
    get_dataset_rows,
    get_datasets,
    get_dataset,
    get_quality_report,
    create_pipeline,
    update_pipeline,
    get_pipelines,
    get_pipeline,
    get_all_users,
    get_user_by_id,
    update_user_role,
    update_user_status,
    get_user_datasets,
    get_user_pipelines,
    get_user_activity,
    log_user_activity,
    insert_data_correction,
    get_data_corrections
)

from backend.quality import (
    load_csv,
    calculate_completeness,
    calculate_validity,
    calculate_uniqueness,
    calculate_consistency,
    calculate_timeliness,
    calculate_quality_score
)

import os
import pandas as pd


app = FastAPI()


# Project folders
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RAW_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "raw"
)

PROCESSED_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

QUARANTINE_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "quarantine"
)


# Upload CSV
@app.post("/upload")
def upload_csv(
    file: UploadFile = File(...),
    current_user=Depends(require_role("Admin", "Data Engineer", "Viewer"))
):

    # Check file type
    if not file.filename.endswith(".csv"):
        return {
            "error": "Only CSV files are allowed"
        }

    # Create folders
    os.makedirs(RAW_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    os.makedirs(QUARANTINE_FOLDER, exist_ok=True)

    # Save uploaded file
    file_path = os.path.join(
        RAW_FOLDER,
        file.filename
    )

    with open(file_path, "wb") as output_file:
        output_file.write(
            file.file.read()
        )

    print("File uploaded:", file.filename)

    profile = profile_csv(file_path)

    print("Dataset Profile:")
    print(profile)

    # Clean data
    clean_data, bad_data = clean_file(
        file_path
    )
    analytics = analyze_dataset(clean_data)
    print("Clean rows:", len(clean_data))
    print("Bad rows:", len(bad_data))
    print("Analytics:")
    print(analytics)

    # Get filename without extension
    name = os.path.splitext(
        file.filename
    )[0]

    # Output paths
    clean_path = os.path.join(
        PROCESSED_FOLDER,
        name + "_clean.csv"
    )

    bad_path = os.path.join(
        QUARANTINE_FOLDER,
        name + "_bad.csv"
    )

    # Save cleaned CSV
    pd.DataFrame(clean_data).to_csv(
        clean_path,
        index=False
    )

    # Save bad records
    pd.DataFrame(bad_data).to_csv(
        bad_path,
        index=False
    )

    # Store clean data in PostgreSQL
    user_id = current_user.get("user_id") if isinstance(current_user, dict) else None
    dataset_id, inserted_rows, version = insert_dataset(
        file.filename,
        clean_data,
        user_id=user_id
    )
    pipeline_id = create_pipeline(dataset_id, user_id=user_id)
    if user_id:
        log_user_activity(
            user_id,
            "DATASET_UPLOAD",
            f"Uploaded dataset {file.filename} (v{version})"
        )

    # Save dataset ID and version-specific CSV copies for precise downloads
    clean_id_path = os.path.join(PROCESSED_FOLDER, f"{dataset_id}_clean.csv")
    clean_v_path = os.path.join(PROCESSED_FOLDER, f"{name}_v{version}_clean.csv")
    pd.DataFrame(clean_data).to_csv(clean_id_path, index=False)
    pd.DataFrame(clean_data).to_csv(clean_v_path, index=False)

    bad_id_path = os.path.join(QUARANTINE_FOLDER, f"{dataset_id}_bad.csv")
    bad_v_path = os.path.join(QUARANTINE_FOLDER, f"{name}_v{version}_bad.csv")
    pd.DataFrame(bad_data).to_csv(bad_id_path, index=False)
    pd.DataFrame(bad_data).to_csv(bad_v_path, index=False)

    # Calculate quality metrics
    rows = load_csv(file_path)

    completeness = calculate_completeness(rows)

    validity = calculate_validity(rows)

    uniqueness = calculate_uniqueness(rows)

    consistency = calculate_consistency(rows)

    timeliness = calculate_timeliness(rows)

    quality_score = calculate_quality_score(
        completeness,
        validity,
        uniqueness,
        consistency,
        timeliness
    )

    # Store quality report
    insert_quality_report(
        dataset_id,
        completeness,
        validity,
        uniqueness,
        consistency,
        timeliness,
        quality_score
    )
    update_pipeline(
        pipeline_id,
        "SUCCESS",
        len(rows),
        len(clean_data),
        len(bad_data)
    )

    print("Quality Score:", quality_score)
    print("Data stored in PostgreSQL!")
    print("Dataset ID:", dataset_id)
    print("Database rows:", inserted_rows)

    # API response
    return {
        "message": "File uploaded, cleaned and stored successfully",
        "filename": file.filename,
        "download_file": name + "_clean.csv",
        "clean_rows": len(clean_data),
        "bad_rows": len(bad_data),
        "profile": profile,
        "analytics": analytics,
        "dataset_id": dataset_id,
        "pipeline_id": pipeline_id,
        "database_rows": inserted_rows,
        "version": version,
        "completeness": completeness,
        "validity": validity,
        "uniqueness": uniqueness,
        "consistency": consistency,
        "timeliness": timeliness,
        "quality_score": quality_score
    }


# Download cleaned CSV
@app.get("/download/{filename}")
def download_clean_file(filename: str):

    file_path = os.path.join(
        PROCESSED_FOLDER,
        filename
    )

    if not os.path.exists(file_path):
        file_path = os.path.join(
            QUARANTINE_FOLDER,
            filename
        )

    if not os.path.exists(file_path):
        return {
            "error": "File not found"
        }

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/csv"
    )


@app.get("/api/v1/datasets/{dataset_id}/download/clean")
def download_clean_dataset(
    dataset_id: int,
    current_user=Depends(get_current_user)
):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    file_name = dataset.get("file_name") or f"dataset_{dataset_id}.csv"
    version = dataset.get("version", 1)
    name = os.path.splitext(file_name)[0]

    candidates = [
        os.path.join(PROCESSED_FOLDER, f"{dataset_id}_clean.csv"),
        os.path.join(PROCESSED_FOLDER, f"{name}_v{version}_clean.csv"),
    ]

    found_path = None
    for path in candidates:
        if os.path.exists(path):
            found_path = path
            break

    if not found_path:
        rows = get_dataset_rows(dataset_id)
        if not rows:
            raise HTTPException(status_code=404, detail="No clean records found for this dataset")

        os.makedirs(PROCESSED_FOLDER, exist_ok=True)
        found_path = os.path.join(PROCESSED_FOLDER, f"{dataset_id}_clean.csv")
        pd.DataFrame(rows).to_csv(found_path, index=False)

    download_filename = f"{name}_v{version}_clean.csv"
    return FileResponse(
        path=found_path,
        filename=download_filename,
        media_type="text/csv"
    )


@app.get("/api/v1/datasets/{dataset_id}/download/rejected")
def download_rejected_dataset(
    dataset_id: int,
    current_user=Depends(get_current_user)
):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    file_name = dataset.get("file_name") or f"dataset_{dataset_id}.csv"
    version = dataset.get("version", 1)
    name = os.path.splitext(file_name)[0]

    candidates = [
        os.path.join(QUARANTINE_FOLDER, f"{dataset_id}_bad.csv"),
        os.path.join(QUARANTINE_FOLDER, f"{name}_v{version}_bad.csv"),
    ]

    found_path = None
    for path in candidates:
        if os.path.exists(path):
            found_path = path
            break

    if not found_path:
        raw_path = os.path.join(RAW_FOLDER, file_name)
        if os.path.exists(raw_path):
            _, bad_data = clean_file(raw_path)
            os.makedirs(QUARANTINE_FOLDER, exist_ok=True)
            found_path = os.path.join(QUARANTINE_FOLDER, f"{dataset_id}_bad.csv")
            pd.DataFrame(bad_data).to_csv(found_path, index=False)
        else:
            fallback = os.path.join(QUARANTINE_FOLDER, f"{name}_bad.csv")
            if os.path.exists(fallback):
                found_path = fallback
            else:
                os.makedirs(QUARANTINE_FOLDER, exist_ok=True)
                found_path = os.path.join(QUARANTINE_FOLDER, f"{dataset_id}_bad.csv")
                pd.DataFrame([]).to_csv(found_path, index=False)

    download_filename = f"{name}_v{version}_rejected.csv"
    return FileResponse(
        path=found_path,
        filename=download_filename,
        media_type="text/csv"
    )
@app.get("/analytics/{dataset_id}")
def get_analytics(
    dataset_id: int,
    current_user=Depends(get_current_user)
):

    rows = get_dataset_rows(dataset_id)

    if not rows:
        return {
            "error": "Dataset not found"
        }

    analytics = analyze_dataset(rows)

    return {
        "dataset_id": dataset_id,
        "rows": len(rows),
        "analytics": analytics
    }
@app.get("/api/v1/datasets")
def list_datasets(
    current_user=Depends(get_current_user)
):

    datasets = get_datasets()

    return {
        "count": len(datasets),
        "datasets": datasets
    }
@app.get("/api/v1/datasets/{dataset_id}")
def get_dataset_details(
    dataset_id: int,
    current_user=Depends(get_current_user)
):

    dataset = get_dataset(dataset_id)

    if dataset is None:
        return {
            "error": "Dataset not found"
        }

    return dataset
@app.get("/api/v1/quality/{dataset_id}")
def get_quality(
    dataset_id: int,
    current_user=Depends(get_current_user)
):

    report = get_quality_report(dataset_id)

    if report is None:
        return {
            "error": "Quality report not found"
        }

    return report
@app.get("/api/v1/kpis")
def get_kpis(
    dataset_id: int,
    current_user=Depends(get_current_user)
):

    rows = get_dataset_rows(dataset_id)

    if not rows:
        return {
            "error": "Dataset not found"
        }

    kpis = calculate_kpis(rows)

    return {
        "dataset_id": dataset_id,
        "kpis": kpis
    }
@app.get("/api/v1/anomalies")
def get_anomalies(
    dataset_id: int,
    current_user=Depends(get_current_user)
):

    rows = get_dataset_rows(dataset_id)

    if not rows:
        return {
            "error": "Dataset not found"
        }

    anomalies = detect_anomalies(rows)

    return {
        "dataset_id": dataset_id,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies
    }
@app.get("/api/v1/pipelines")
def list_pipelines(
    current_user=Depends(get_current_user)
):

    pipelines = get_pipelines()

    return {
        "count": len(pipelines),
        "pipelines": pipelines
    }
@app.get("/api/v1/pipelines/{pipeline_id}")
def get_pipeline_details(
    pipeline_id: int,
    current_user=Depends(get_current_user)
):

    pipeline = get_pipeline(pipeline_id)

    if pipeline is None:
        return {
            "error": "Pipeline not found"
        }

    return pipeline


def load_rejected_rows_for_dataset(dataset):
    if not dataset:
        return []
    dataset_id = dataset.get("id") or dataset.get("dataset_id")
    file_name = dataset.get("file_name") or f"dataset_{dataset_id}.csv"
    version = dataset.get("version", 1)
    name = os.path.splitext(file_name)[0]

    candidates = [
        os.path.join(QUARANTINE_FOLDER, f"{dataset_id}_bad.csv"),
        os.path.join(QUARANTINE_FOLDER, f"{name}_v{version}_bad.csv"),
        os.path.join(QUARANTINE_FOLDER, f"{name}_bad.csv")
    ]

    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                return df.fillna("").astype(str).to_dict(orient="records")
            except Exception:
                pass
    return []


class CorrectionRequest(BaseModel):
    row_index: int
    column_name: str
    new_value: str
    source: str = "clean"


@app.get("/api/v1/datasets/{dataset_id}/records")
def get_dataset_records(
    dataset_id: int,
    current_user=Depends(get_current_user)
):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    clean_rows = get_dataset_rows(dataset_id)
    rejected_rows = load_rejected_rows_for_dataset(dataset)

    columns = []
    if clean_rows and len(clean_rows) > 0:
        columns = list(clean_rows[0].keys())
    elif rejected_rows and len(rejected_rows) > 0:
        columns = list(rejected_rows[0].keys())

    return {
        "dataset_id": dataset_id,
        "file_name": dataset.get("file_name"),
        "version": dataset.get("version"),
        "columns": columns,
        "clean_rows": clean_rows,
        "rejected_rows": rejected_rows
    }


@app.get("/api/v1/datasets/{dataset_id}/audit")
def get_dataset_audit(
    dataset_id: int,
    current_user=Depends(get_current_user)
):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    corrections = get_data_corrections(dataset_id)
    return {
        "dataset_id": dataset_id,
        "corrections": corrections
    }


@app.post("/api/v1/datasets/{dataset_id}/correct")
def correct_dataset_record(
    dataset_id: int,
    request: CorrectionRequest,
    current_user=Depends(require_role("Admin", "Data Engineer"))
):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    file_name = dataset.get("file_name") or f"dataset_{dataset_id}.csv"
    prev_version = dataset.get("version", 1)
    user_id = current_user.get("user_id")
    username = current_user.get("username", "user")

    clean_rows = get_dataset_rows(dataset_id)
    rejected_rows = load_rejected_rows_for_dataset(dataset)

    old_value = ""

    if request.source == "rejected":
        if not (0 <= request.row_index < len(rejected_rows)):
            raise HTTPException(status_code=400, detail="Invalid rejected row index")
        target_row = rejected_rows[request.row_index]
        old_value = target_row.get(request.column_name, "")
        target_row[request.column_name] = request.new_value
    else:
        if not (0 <= request.row_index < len(clean_rows)):
            raise HTTPException(status_code=400, detail="Invalid clean row index")
        target_row = clean_rows[request.row_index]
        old_value = target_row.get(request.column_name, "")
        target_row[request.column_name] = request.new_value

    raw_rows = clean_rows + rejected_rows
    if not raw_rows:
        raise HTTPException(status_code=400, detail="No rows available for processing")

    name = os.path.splitext(file_name)[0]
    os.makedirs(RAW_FOLDER, exist_ok=True)
    temp_raw_path = os.path.join(RAW_FOLDER, f"{name}_temp_correct.csv")
    pd.DataFrame(raw_rows).to_csv(temp_raw_path, index=False)

    clean_data, bad_data = clean_file(temp_raw_path)

    new_dataset_id, inserted_rows, new_version = insert_dataset(
        file_name,
        clean_data,
        user_id=user_id
    )

    pipeline_id = create_pipeline(new_dataset_id, user_id=user_id)

    if user_id:
        log_user_activity(
            user_id,
            "DATASET_CORRECTION",
            f"Corrected {request.column_name} from '{old_value}' to '{request.new_value}' in {file_name} (v{prev_version} -> v{new_version})"
        )

    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    os.makedirs(QUARANTINE_FOLDER, exist_ok=True)

    clean_id_path = os.path.join(PROCESSED_FOLDER, f"{new_dataset_id}_clean.csv")
    clean_v_path = os.path.join(PROCESSED_FOLDER, f"{name}_v{new_version}_clean.csv")
    pd.DataFrame(clean_data).to_csv(clean_id_path, index=False)
    pd.DataFrame(clean_data).to_csv(clean_v_path, index=False)

    bad_id_path = os.path.join(QUARANTINE_FOLDER, f"{new_dataset_id}_bad.csv")
    bad_v_path = os.path.join(QUARANTINE_FOLDER, f"{name}_v{new_version}_bad.csv")
    pd.DataFrame(bad_data).to_csv(bad_id_path, index=False)
    pd.DataFrame(bad_data).to_csv(bad_v_path, index=False)

    rows_for_quality = load_csv(temp_raw_path)
    completeness = calculate_completeness(rows_for_quality)
    validity = calculate_validity(rows_for_quality)
    uniqueness = calculate_uniqueness(rows_for_quality)
    consistency = calculate_consistency(rows_for_quality)
    timeliness = calculate_timeliness(rows_for_quality)
    quality_score = calculate_quality_score(
        completeness, validity, uniqueness, consistency, timeliness
    )

    insert_quality_report(
        new_dataset_id,
        completeness,
        validity,
        uniqueness,
        consistency,
        timeliness,
        quality_score
    )

    update_pipeline(
        pipeline_id,
        "SUCCESS",
        len(raw_rows),
        len(clean_data),
        len(bad_data)
    )

    insert_data_correction(
        new_dataset_id,
        prev_version,
        new_version,
        user_id,
        username,
        request.row_index,
        request.column_name,
        old_value,
        request.new_value
    )

    if os.path.exists(temp_raw_path):
        try:
            os.remove(temp_raw_path)
        except Exception:
            pass

    return {
        "success": True,
        "message": "Correction saved. New dataset version created.",
        "dataset_id": new_dataset_id,
        "previous_version": prev_version,
        "new_version": new_version,
        "clean_rows": len(clean_data),
        "bad_rows": len(bad_data),
        "quality_score": quality_score,
        "pipeline_id": pipeline_id,
        "audit": {
            "dataset_id": new_dataset_id,
            "previous_version": prev_version,
            "new_version": new_version,
            "user_id": user_id,
            "username": username,
            "row_index": request.row_index,
            "column_name": request.column_name,
            "old_value": old_value,
            "new_value": request.new_value,
            "source": request.source
        }
    }


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "Viewer"
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/v1/auth/register")
def register(request: RegisterRequest):

    # Public registration ALWAYS assigns Viewer role
    success, result = register_user(
        request.username,
        request.email,
        request.password,
        role="Viewer"
    )

    if not success:
        return {
            "success": False,
            "message": result
        }

    return {
        "success": True,
        "message": "User registered successfully",
        "user_id": result
    }
@app.post("/api/v1/auth/login")
def login(request: LoginRequest):

    success, result = login_user(
        request.username,
        request.password
    )

    if not success:
        return {
            "success": False,
            "message": result
        }

    return {
        "success": True,
        "message": "Login successful",
        "access_token": result,
        "token_type": "bearer"
    }
@app.get("/api/v1/auth/me")
def get_me(current_user=Depends(get_current_user)):

    return {
        "success": True,
        "user": current_user
    }
@app.get("/api/v1/auth/admin-test")
def admin_test(
    current_user=Depends(require_role("Admin"))
):

    return {
        "success": True,
        "message": "Admin access granted",
        "user": current_user
    }


@app.get("/api/v1/users")
def get_users(
    current_user=Depends(require_role("Admin"))
):
    return get_all_users()


class UpdateRoleRequest(BaseModel):
    role: str


class UpdateStatusRequest(BaseModel):
    status: str
    confirm_self: bool = False


@app.get("/api/v1/users/{user_id}")
def get_user_details(
    user_id: int,
    current_user=Depends(require_role("Admin"))
):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    datasets = get_user_datasets(user_id)
    pipelines = get_user_pipelines(user_id)
    activity = get_user_activity(user_id)

    return {
        "user": user,
        "datasets": datasets,
        "pipelines": pipelines,
        "recent_activity": activity,
        "summary": {
            "total_datasets": len(datasets),
            "total_pipelines": len(pipelines),
            "total_activities": len(activity)
        },
        "ownership_note": "Historical datasets and pipelines uploaded before user tracking have unassigned ownership."
    }


@app.put("/api/v1/users/{user_id}/role")
def change_user_role(
    user_id: int,
    request: UpdateRoleRequest,
    current_user=Depends(require_role("Admin"))
):
    valid_roles = ["Admin", "Data Engineer", "Viewer"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Role must be one of: {', '.join(valid_roles)}"
        )

    if current_user.get("user_id") == user_id:
        raise HTTPException(
            status_code=400,
            detail="Users cannot change their own role"
        )

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = update_user_role(user_id, request.role)
    log_user_activity(
        user_id,
        "ROLE_CHANGE",
        f"Role changed from {user['role']} to {request.role} by {current_user.get('username')}"
    )

    return {
        "success": True,
        "message": f"User role updated to {request.role}",
        "user": updated_user
    }


@app.put("/api/v1/users/{user_id}/status")
def change_user_status(
    user_id: int,
    request: UpdateStatusRequest,
    current_user=Depends(require_role("Admin"))
):
    if request.status not in ["active", "inactive"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Status must be 'active' or 'inactive'"
        )

    if current_user.get("user_id") == user_id and request.status == "inactive" and not request.confirm_self:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required to deactivate your own account"
        )

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = update_user_status(user_id, request.status)
    log_user_activity(
        user_id,
        "STATUS_CHANGE",
        f"Account status changed to {request.status} by {current_user.get('username')}"
    )

    return {
        "success": True,
        "message": f"User status updated to {request.status}",
        "user": updated_user
    }
