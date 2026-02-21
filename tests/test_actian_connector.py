"""
tests for the actian connector (mocked gRPC calls)
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_check_available_returns_false_when_no_server():
    """should return False when actian is not reachable"""
    # reset cached stub
    import utils.actian_connector as ac
    ac._stub = None
    ac._pb2 = None
    ac._pb2_grpc = None
    ac.ACTIAN_PORT = "99999"  # unreachable port

    result = ac._check_actian_available()
    assert result is False

    # restore
    ac.ACTIAN_PORT = "50051"
    ac._stub = None


def test_search_returns_none_when_unavailable():
    """should return None gracefully when actian is not available"""
    import utils.actian_connector as ac
    ac._stub = None
    ac._pb2 = None
    ac._pb2_grpc = None
    ac.ACTIAN_PORT = "99999"

    result = ac.search_similar_projects("test_code", df_projects=pd.DataFrame())
    assert result is None

    ac.ACTIAN_PORT = "50051"
    ac._stub = None


def test_upsert_returns_false_when_unavailable():
    """should return False when actian is not available"""
    import utils.actian_connector as ac
    ac._stub = None
    ac._pb2 = None
    ac._pb2_grpc = None
    ac.ACTIAN_PORT = "99999"

    result = ac.upsert_project_vectors(pd.DataFrame())
    assert result is False

    ac.ACTIAN_PORT = "50051"
    ac._stub = None


def test_initialize_collection_returns_false_when_unavailable():
    """should return False when actian is not available"""
    import utils.actian_connector as ac
    ac._stub = None
    ac._pb2 = None
    ac._pb2_grpc = None
    ac.ACTIAN_PORT = "99999"

    result = ac.initialize_collection(19)
    assert result is False

    ac.ACTIAN_PORT = "50051"
    ac._stub = None
