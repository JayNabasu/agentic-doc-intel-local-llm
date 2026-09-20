import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import (
    AnalyzeDocumentRequest, DocumentType, DocumentAnalysisResult
)
from backend.extractor_service import ExtractorService
from backend.cache import DocumentIntelligenceCache

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "qwen2.5:7b" in data["supported_models"]

def test_benchmarks_endpoint():
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert len(data["models_evaluated"]) == 2
    assert data["models_evaluated"][0]["model"] == "qwen2.5:7b"

def test_analyze_document_endpoint():
    sample_text = """
    SOLUTION DESIGN DOCUMENT: SUBSEA PIPELINE TELEMETRY AUTOMATION
    Document Ref: NNPC-ENG-SDD-OML119-004
    Operating Asset: OML 119 Deepwater Field
    Budget: $4,500,000.00 USD
    SLA: 99.9% uptime
    """
    payload = {
        "document_text": sample_text,
        "document_type": "SOLUTION_DESIGN_DOCUMENT",
        "model_name": "qwen2.5:7b",
        "use_cache": True
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["document_type"] == "SOLUTION_DESIGN_DOCUMENT"
    assert len(result["extracted_entities"]) > 0
    assert result["completeness_score"] >= 80.0

def test_cache_hit_ratio_increase():
    cache = DocumentIntelligenceCache()
    key = cache.compute_cache_key("Sample text for cache verification", "qwen2.5:7b")
    
    # Initial miss
    assert cache.get(key) is None
    
    # Store
    cache.set(key, {"mock": "data"})
    
    # Hit
    cached = cache.get(key)
    assert cached == {"mock": "data"}
    
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_ratio_pct"] == 50.0
