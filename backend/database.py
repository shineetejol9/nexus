import psycopg2
import json
import os

from dotenv import load_dotenv

load_dotenv()
# Create PostgreSQL connection
def get_connection():

    connection = psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        port=os.getenv("DATABASE_PORT")
    )

    return connection


# Insert uploaded dataset and clean rows
def insert_dataset(file_name, clean_data, user_id=None):

    connection = get_connection()

    print("Connected to NEXUS database!")

    cursor = connection.cursor()

    # Find latest version of this file
    cursor.execute("""
        SELECT COALESCE(MAX(version), 0)
        FROM datasets
        WHERE file_name = %s
    """, (file_name,))

    latest_version = cursor.fetchone()[0]

    new_version = latest_version + 1

    # Create dataset record
    if user_id is not None:
        cursor.execute("""
            INSERT INTO datasets (file_name, version, user_id)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (file_name, new_version, user_id))
    else:
        cursor.execute("""
            INSERT INTO datasets (file_name, version)
            VALUES (%s, %s)
            RETURNING id
        """, (file_name, new_version))

    dataset_id = cursor.fetchone()[0]

    print("Dataset ID:", dataset_id)
    print("Version:", new_version)

    # Insert clean rows
    row_count = 0

    for row in clean_data:

        cursor.execute("""
            INSERT INTO dataset_rows (dataset_id, row_data)
            VALUES (%s, %s)
        """, (
            dataset_id,
            json.dumps(row)
        ))

        row_count += 1

    connection.commit()

    print("Rows inserted:", row_count)

    cursor.close()
    connection.close()

    return dataset_id, row_count, new_version


# Insert quality report
def insert_quality_report(
    dataset_id,
    completeness,
    validity,
    uniqueness,
    consistency,
    timeliness,
    quality_score
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO quality_reports
        (
            dataset_id,
            completeness,
            validity,
            uniqueness,
            consistency,
            timeliness,
            quality_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        dataset_id,
        completeness,
        validity,
        uniqueness,
        consistency,
        timeliness,
        quality_score
    ))

    connection.commit()

    cursor.close()
    connection.close()

    print("Quality report stored!")
def get_dataset(dataset_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, file_name, version, uploaded_at
        FROM datasets
        WHERE id = %s
    """, (dataset_id,))

    dataset = cursor.fetchone()

    if dataset is None:
        cursor.close()
        connection.close()
        return None

    cursor.execute("""
        SELECT row_data
        FROM dataset_rows
        WHERE dataset_id = %s
    """, (dataset_id,))

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "id": dataset[0],
        "file_name": dataset[1],
        "version": dataset[2],
        "uploaded_at": dataset[3],
        "rows": [row[0] for row in rows]
    }
def get_dataset_rows(dataset_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT row_data
        FROM dataset_rows
        WHERE dataset_id = %s
    """, (dataset_id,))

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [row[0] for row in rows]
def get_datasets():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, file_name, version, uploaded_at
        FROM datasets
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    datasets = []

    for row in rows:
        datasets.append({
            "id": row[0],
            "file_name": row[1],
            "version": row[2],
            "uploaded_at": row[3]
        })

    return datasets
def get_quality_report(dataset_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT completeness,
               validity,
               uniqueness,
               consistency,
               timeliness,
               quality_score,
               created_at
        FROM quality_reports
        WHERE dataset_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (dataset_id,))

    report = cursor.fetchone()

    cursor.close()
    connection.close()

    if report is None:
        return None

    return {
        "dataset_id": dataset_id,
        "completeness": report[0],
        "validity": report[1],
        "uniqueness": report[2],
        "consistency": report[3],
        "timeliness": report[4],
        "quality_score": report[5],
        "created_at": report[6]
    }
def create_pipeline(dataset_id, user_id=None):
    connection = get_connection()
    cursor = connection.cursor()

    if user_id is not None:
        cursor.execute("""
            INSERT INTO pipelines(dataset_id, status, user_id)
            VALUES(%s, %s, %s)
            RETURNING id
        """, (dataset_id, "RUNNING", user_id))
    else:
        cursor.execute("""
            INSERT INTO pipelines(dataset_id, status)
            VALUES(%s, %s)
            RETURNING id
        """, (dataset_id, "RUNNING"))

    pipeline_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return pipeline_id
def update_pipeline(
    pipeline_id,
    status,
    total_rows,
    clean_rows,
    bad_rows
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE pipelines
        SET status = %s,
            completed_at = CURRENT_TIMESTAMP,
            total_rows = %s,
            clean_rows = %s,
            bad_rows = %s
        WHERE id = %s
    """, (
        status,
        total_rows,
        clean_rows,
        bad_rows,
        pipeline_id
    ))

    connection.commit()
    cursor.close()
    connection.close()
def get_pipelines():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id,
               dataset_id,
               status,
               started_at,
               completed_at,
               total_rows,
               clean_rows,
               bad_rows
        FROM pipelines
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    pipelines = []

    for row in rows:
        pipelines.append({
            "id": row[0],
            "dataset_id": row[1],
            "status": row[2],
            "started_at": row[3],
            "completed_at": row[4],
            "total_rows": row[5],
            "clean_rows": row[6],
            "bad_rows": row[7]
        })

    return pipelines
def get_pipeline(pipeline_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id,
               dataset_id,
               status,
               started_at,
               completed_at,
               total_rows,
               clean_rows,
               bad_rows
        FROM pipelines
        WHERE id = %s
    """, (pipeline_id,))

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "dataset_id": row[1],
        "status": row[2],
        "started_at": row[3],
        "completed_at": row[4],
        "total_rows": row[5],
        "clean_rows": row[6],
        "bad_rows": row[7]
    }


def get_all_users():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, email, role, created_at, status
        FROM users
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    users = []
    for row in rows:
        created_at_val = row[4]
        if hasattr(created_at_val, "isoformat"):
            created_at_val = created_at_val.isoformat()
        elif created_at_val is not None:
            created_at_val = str(created_at_val)

        status_val = row[5] if len(row) > 5 and row[5] is not None else "active"

        users.append({
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "role": row[3],
            "status": status_val,
            "created_at": created_at_val
        })

    return users


def get_user_by_id(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, email, role, status, created_at
        FROM users
        WHERE id = %s
    """, (user_id,))

    row = cursor.fetchone()
    cursor.close()
    connection.close()

    if row is None:
        return None

    created_at_val = row[5]
    if hasattr(created_at_val, "isoformat"):
        created_at_val = created_at_val.isoformat()
    elif created_at_val is not None:
        created_at_val = str(created_at_val)

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "role": row[3],
        "status": row[4] or "active",
        "created_at": created_at_val
    }


def update_user_role(user_id, new_role):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET role = %s
        WHERE id = %s
        RETURNING id, username, email, role, status, created_at
    """, (new_role, user_id))

    row = cursor.fetchone()
    connection.commit()
    cursor.close()
    connection.close()

    if row is None:
        return None

    created_at_val = row[5]
    if hasattr(created_at_val, "isoformat"):
        created_at_val = created_at_val.isoformat()
    elif created_at_val is not None:
        created_at_val = str(created_at_val)

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "role": row[3],
        "status": row[4] or "active",
        "created_at": created_at_val
    }


def update_user_status(user_id, new_status):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET status = %s
        WHERE id = %s
        RETURNING id, username, email, role, status, created_at
    """, (new_status, user_id))

    row = cursor.fetchone()
    connection.commit()
    cursor.close()
    connection.close()

    if row is None:
        return None

    created_at_val = row[5]
    if hasattr(created_at_val, "isoformat"):
        created_at_val = created_at_val.isoformat()
    elif created_at_val is not None:
        created_at_val = str(created_at_val)

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "role": row[3],
        "status": row[4] or "active",
        "created_at": created_at_val
    }


def get_user_datasets(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, file_name, version, uploaded_at
        FROM datasets
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    datasets = []
    for r in rows:
        uploaded_at_val = r[3]
        if hasattr(uploaded_at_val, "isoformat"):
            uploaded_at_val = uploaded_at_val.isoformat()
        elif uploaded_at_val is not None:
            uploaded_at_val = str(uploaded_at_val)
        datasets.append({
            "id": r[0],
            "file_name": r[1],
            "version": r[2],
            "uploaded_at": uploaded_at_val
        })
    return datasets


def get_user_pipelines(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, dataset_id, status, started_at, completed_at, total_rows, clean_rows, bad_rows
        FROM pipelines
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    pipelines = []
    for r in rows:
        started_at = r[3].isoformat() if hasattr(r[3], "isoformat") else str(r[3]) if r[3] else None
        completed_at = r[4].isoformat() if hasattr(r[4], "isoformat") else str(r[4]) if r[4] else None
        pipelines.append({
            "id": r[0],
            "dataset_id": r[1],
            "status": r[2],
            "started_at": started_at,
            "completed_at": completed_at,
            "total_rows": r[5],
            "clean_rows": r[6],
            "bad_rows": r[7]
        })
    return pipelines


def get_user_activity(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, activity_type, description, created_at
        FROM user_activity
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 20
    """, (user_id,))

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    activity = []
    for r in rows:
        created_at_val = r[3].isoformat() if hasattr(r[3], "isoformat") else str(r[3]) if r[3] else None
        activity.append({
            "id": r[0],
            "activity_type": r[1],
            "description": r[2],
            "created_at": created_at_val
        })
    return activity


def log_user_activity(user_id, activity_type, description):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO user_activity (user_id, activity_type, description)
            VALUES (%s, %s, %s)
        """, (user_id, activity_type, description))
        connection.commit()
        cursor.close()
        connection.close()
    except Exception:
        pass


def insert_data_correction(dataset_id, previous_version, new_version, user_id, username, row_index, column_name, old_value, new_value):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_corrections (
                id SERIAL PRIMARY KEY,
                dataset_id INT,
                previous_version INT,
                new_version INT,
                user_id INT,
                username VARCHAR(255),
                row_index INT,
                column_name VARCHAR(255),
                old_value TEXT,
                new_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO data_corrections
            (dataset_id, previous_version, new_version, user_id, username, row_index, column_name, old_value, new_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            dataset_id,
            previous_version,
            new_version,
            user_id,
            username,
            row_index,
            column_name,
            str(old_value) if old_value is not None else "",
            str(new_value) if new_value is not None else ""
        ))
        correction_id = cursor.fetchone()[0]
        connection.commit()
        cursor.close()
        connection.close()
        return correction_id
    except Exception as e:
        print("Data correction insert error:", e)
        return None


def get_data_corrections(dataset_id):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, dataset_id, previous_version, new_version, user_id, username, row_index, column_name, old_value, new_value, created_at
            FROM data_corrections
            WHERE dataset_id = %s OR new_version = (SELECT version FROM datasets WHERE id = %s)
            ORDER BY id DESC
        """, (dataset_id, dataset_id))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        corrections = []
        for r in rows:
            created_at_val = r[10].isoformat() if hasattr(r[10], "isoformat") else str(r[10]) if r[10] else None
            corrections.append({
                "id": r[0],
                "dataset_id": r[1],
                "previous_version": r[2],
                "new_version": r[3],
                "user_id": r[4],
                "username": r[5],
                "row_index": r[6],
                "column_name": r[7],
                "old_value": r[8],
                "new_value": r[9],
                "created_at": created_at_val
            })
        return corrections
    except Exception:
        return []

