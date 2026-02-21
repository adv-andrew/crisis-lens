"""
CrisisLens Actian VectorAI DB Connector
========================================
gRPC connector for Actian VectorAI DB (sponsor challenge).
Docker: docker pull williamimoh/actian-vectorai-db:1.0b
       docker run -d -p 50051:50051 williamimoh/actian-vectorai-db:1.0b

All Actian DB interactions go through this module.
If Actian is unavailable, callers fall back to similarity_engine.py (sklearn).
"""

import json
import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ACTIAN_HOST = os.getenv("ACTIAN_HOST", "localhost")
ACTIAN_PORT = os.getenv("ACTIAN_PORT", "50051")
COLLECTION_NAME = "hrp_projects"

_stub = None
_pb2 = None
_pb2_grpc = None


def _get_stub():
    """lazy-load grpc stub to avoid import errors when grpc is not installed"""
    global _stub, _pb2, _pb2_grpc
    if _stub is not None:
        return _stub

    import grpc

    from proto import vdss_pb2, vdss_pb2_grpc

    _pb2 = vdss_pb2
    _pb2_grpc = vdss_pb2_grpc
    channel = grpc.insecure_channel(f"{ACTIAN_HOST}:{ACTIAN_PORT}")
    _stub = vdss_pb2_grpc.VDSSServiceStub(channel)
    return _stub


def _check_actian_available() -> bool:
    """ping actian endpoint, returns True if reachable"""
    try:
        stub = _get_stub()
        resp = stub.HealthCheck(_pb2.HealthCheckRequest())
        return resp.status.code == 0
    except Exception:
        return False


def initialize_collection(dimension: int) -> bool:
    """create and open the hrp_projects collection, returns True on success"""
    try:
        stub = _get_stub()

        # try to open existing first
        resp = stub.OpenCollection(_pb2.OpenCollectionRequest(collection_name=COLLECTION_NAME))
        if resp.status.code == 0:
            # check if already populated
            count_resp = stub.GetVectorCount(_pb2.GetVectorCountRequest(collection_name=COLLECTION_NAME))
            if count_resp.count > 0:
                return True

        # create fresh
        config = _pb2.CollectionConfig(
            index_driver=_pb2.FAISS,
            index_algorithm=_pb2.HNSW,
            storage_type=_pb2.MEM,
            dimension=dimension,
            distance_metric=_pb2.COSINE,
        )
        resp = stub.CreateCollection(_pb2.CreateCollectionRequest(
            collection_name=COLLECTION_NAME,
            config=config,
        ))
        if resp.status.code != 0:
            # might already exist, try open
            pass

        resp = stub.OpenCollection(_pb2.OpenCollectionRequest(collection_name=COLLECTION_NAME))
        return resp.status.code == 0
    except Exception:
        return False


def upsert_project_vectors(df_projects: pd.DataFrame) -> bool:
    """store project feature vectors in actian VectorAI DB, returns True on success"""
    if not _check_actian_available():
        return False

    try:
        from utils.similarity_engine import build_feature_matrix

        X, enc, scaler, df_feat = build_feature_matrix(df_projects)
        X_dense = X.toarray()
        dim = X_dense.shape[1]

        if not initialize_collection(dim):
            return False

        stub = _get_stub()

        # batch upsert in chunks
        batch_size = 500
        total = X_dense.shape[0]

        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)

            vector_ids = []
            vectors = []
            payloads = []

            for j in range(i, end_idx):
                row = df_feat.iloc[j]
                vector_ids.append(_pb2.VectorIdentifier(u64_id=j))
                vectors.append(_pb2.Vector(data=X_dense[j].tolist(), dimension=dim))
                payload_data = {
                    "idx": j,
                    "project_code": str(row.get("project_code", "")),
                    "country_iso3": str(row.get("country_iso3", "")),
                    "cluster_name": str(row.get("cluster_name", "")),
                    "budget_usd": float(row.get("budget_usd", 0) or 0),
                    "beneficiaries_total": float(row.get("beneficiaries_total", 0) or 0),
                    "project_title": str(row.get("project_title", ""))[:100],
                    "efficiency_ratio": float(row.get("efficiency_ratio", 0) or 0),
                }
                payloads.append(_pb2.Payload(json=json.dumps(payload_data)))

            resp = stub.BatchUpsert(_pb2.BatchUpsertRequest(
                collection_name=COLLECTION_NAME,
                vector_ids=vector_ids,
                vectors=vectors,
                payloads=payloads,
            ))
            if resp.status.code != 0:
                return False

        return True
    except Exception:
        return False


def search_similar_projects(
    project_code: str,
    df_projects: pd.DataFrame | None = None,
    top_n: int = 5,
) -> pd.DataFrame | None:
    """query actian for nearest neighbors, returns DataFrame or None if unavailable"""
    if not _check_actian_available():
        return None

    try:
        stub = _get_stub()

        # check if collection has data
        count_resp = stub.GetVectorCount(_pb2.GetVectorCountRequest(collection_name=COLLECTION_NAME))
        if count_resp.count == 0:
            # need to populate first
            if df_projects is not None:
                if not upsert_project_vectors(df_projects):
                    return None
            else:
                return None

        # build query vector for the given project
        if df_projects is None:
            return None

        from utils.similarity_engine import build_feature_matrix
        X, enc, scaler, df_feat = build_feature_matrix(df_projects)

        query_mask = df_feat["project_code"] == project_code
        if not query_mask.any():
            return None

        query_idx = query_mask.values.argmax()
        query_vec = X[query_idx].toarray()[0].tolist()
        dim = X.shape[1]

        # search (top_n + 1 to exclude self)
        resp = stub.Search(_pb2.SearchRequest(
            collection_name=COLLECTION_NAME,
            query=_pb2.Vector(data=query_vec, dimension=dim),
            top_k=top_n + 1,
            with_payload=True,
        ))

        if resp.status.code != 0 or not resp.results:
            return None

        # parse results, exclude the query project itself
        records = []
        for r in resp.results:
            payload = json.loads(r.payload.json) if r.payload.json else {}
            if payload.get("project_code") == project_code:
                continue
            records.append({
                "project_code": payload.get("project_code", ""),
                "country_iso3": payload.get("country_iso3", ""),
                "cluster_name": payload.get("cluster_name", ""),
                "budget_usd": payload.get("budget_usd", 0),
                "beneficiaries_total": payload.get("beneficiaries_total", 0),
                "efficiency_ratio": payload.get("efficiency_ratio", 0),
                "project_title": payload.get("project_title", ""),
                "similarity_score": float(r.score),
            })

        if not records:
            return None

        return pd.DataFrame(records[:top_n])
    except Exception:
        return None
