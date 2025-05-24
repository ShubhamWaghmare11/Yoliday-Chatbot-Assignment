"""
tests/alltests.py

This module contains unit and integration tests for the Yoliday LLP assignment backend, built using FastAPI and Streamlit.
Tests are written using pytest, with FastAPI's TestClient and unittest.mock for mocking dependencies like Groq API calls
and Supabase Postgre database operations.

Test Coverage:
--------------
1. Prompt Formatting:
   - Verifies that generated prompts follow expected structure and contain required keys.
   - Functions: `test_build_prompt`, `test_build_refine_prompt`

2. API Endpoint Validation:
   - Ensures correct behavior of `/generate` and `/history` endpoints under various conditions:
       - Valid input
       - Missing parameters
       - Wrong data types
   - Functions: `test_generate_endpoint_prompt_formatting`, `test_generate_endpoint_missing_params`, 
                `test_generate_endpoint_missing_query`, `test_generate_endpoint_wrong_data_types`,
                `test_history_endpoint_missing_user_id`, `test_history_valid_user_id`

3. Database Logic:
   - Mocks Supabase operations to test logic in `db.crud`:
       - Entry creation (`add_entry`)
       - History retrieval (`get_history`)
   - Functions: `test_add_entry_success`, `test_get_history_success`

4. Integration Test:
   - Simulates an end-to-end flow from sending a query to retrieving chat history.
   - Function: `test_complete_flow`

Mocks:
------
- `ChatGroq.invoke`: Mocked to simulate AI model responses.
- `db.crud.add_entry`: Mocked to avoid actual DB insertions.
- `db.crud.supabase`: Mocked to simulate Supabase query chaining and results.

Usage:
------
Run with pytest:
    pytest tests/alltests.py
"""

import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend import app
from utils.prompts import build_prompt, build_refine_prompt
from langchain_groq import ChatGroq
from db import crud

# Initialize FastAPI test client
client = TestClient(app)

# Sample input for testing
TEST_USER_ID = "abc123"
TEST_QUERY = "Explain blockchain"


def test_generate_endpoint_prompt_formatting():
    """Test the /generate endpoint to verify prompt formatting logic."""
    # Mock response for ChatGroq
    mock_response = {
        "casual_response": "Blockchain is like a super secure digital ledger, kinda like a shared Google Doc!",
        "formal_response": "A blockchain is a decentralized, immutable ledger that records transactions across a network."
    }
    
    with patch.object(ChatGroq,"invoke",new=MagicMock()) as mock_model:
        # Mock the initial and refinement responses
        mock_model.side_effect = [
            type("MockResponse", (), {"content": json.dumps(mock_response)}),  # Initial response
            type("MockResponse", (), {"content": json.dumps(mock_response)})   # Refined response
        ]

        # Mock add_entry to avoid database calls
        with patch("db.crud.add_entry") as mock_add_entry:
            # Send POST request to /generate
            response = client.post(
                "/generate",
                json={"user_id": TEST_USER_ID, "query": TEST_QUERY,"groq_api_key":"mock_key"}
            )

            # Check response status and structure
            assert response.status_code == 200
            data = response.json()
            assert "output" in data


def test_build_prompt():
    prompt = build_prompt("blockchain")
    assert '"casual_response"' in prompt
    assert '"formal_response"' in prompt
    assert "Output ONLY the JSON dictionary" in prompt

def test_build_refine_prompt():
    prompt = build_refine_prompt({'casual_response':'Mock','formal_response':'mock'})
    assert "'casual_response'" in prompt
    assert "'formal_response'" in prompt
    assert "Output only the refined JSON dictionary" in prompt
    assert "Input JSON" in prompt

def test_generate_endpoint_missing_params():
    response = client.post("/generate",json={'query':"Explain AI"})
    assert response.status_code == 422
    assert "user_id" in response.text
    assert "groq_api_key" in response.text


def test_generate_endpoint_missing_query():
    response = client.post("/generate",json={'user_id':"user123"})
    assert response.status_code == 422
    assert "query" in response.text
    


def test_generate_endpoint_wrong_data_types():
    response = client.post("/generate", json={"user_id": 123, "query": True,'groq_api_key':'mock key'})
    assert response.status_code == 422


def test_history_endpoint_missing_user_id():
    response = client.get("/history")
    assert response.status_code == 422
    assert "detail" in response.json()


def test_history_valid_user_id():
    mock_history = [
        {
            "query": "What is AI?",
            "casual_response": "It's like a smart robot brain.",
            "formal_response": "Artificial intelligence (AI) is the simulation of human intelligence processes by machines.",
            "created_at": "2024-01-01T00:00:00"
        }
    ]

    # Create a fake result object with mappings().all()
    with patch("db.crud.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_history
        mock_supabase.table.return_value = mock_table

        response = client.get("/history?user_id=abc123")

        assert response.status_code == 200
        assert "output" in response.json()
        assert response.json()["output"] == mock_history



def test_add_entry_success():
    # Mock the chained supabase calls for insert().execute()
    mock_execute = MagicMock()
    mock_table = MagicMock()
    mock_table.insert.return_value = mock_table  # insert returns self for chaining
    mock_table.execute = mock_execute
    mock_execute.return_value = {"status_code": 201}  # fake successful response

    with patch.object(crud.supabase, "table", return_value=mock_table) as mock_table_fn:
        result = crud.add_entry("user1", "query", "casual", "formal")
        
        # Assertions
        mock_table_fn.assert_called_once_with("prompts")
        mock_table.insert.assert_called_once_with({
            "user_id": "user1",
            "query": "query",
            "casual_response": "casual",
            "formal_response": "formal"
        })
        mock_execute.assert_called_once()
        assert result is True


def test_get_history_success():
    mock_execute = MagicMock()
    mock_execute.return_value.data = [{"id": 1, "query": "test"}]

    mock_order = MagicMock()
    mock_order.execute = mock_execute

    mock_eq = MagicMock()
    mock_eq.order.return_value = mock_order

    mock_select = MagicMock()
    mock_select.eq.return_value = mock_eq

    mock_table = MagicMock()
    mock_table.select.return_value = mock_select

    with patch.object(crud.supabase, "table", return_value=mock_table) as mock_table_fn:
        result = crud.get_history("user1")

        # Check call chain
        mock_table_fn.assert_called_once_with("prompts")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("user_id", "user1")
        mock_eq.order.assert_called_once_with("created_at", desc=True)
        mock_order.execute.assert_called_once()
        assert isinstance(result, list)
        assert result[0]["query"] == "test"


def test_complete_flow():
    user_id = "testuser"
    query = "Explain quantum computing"

    mock_response = {
        "casual_response": "It's like magic computers that can think in probabilities",
        "formal_response": "Quantum computing utilizes quantum bits that can exist in superpositions"
    }

    # Patch the ChatGroq model call
    with patch.object(ChatGroq, "invoke", new=MagicMock()) as mock_model:
        mock_model.side_effect = [
            type("MockResponse", (), {"content": json.dumps(mock_response)}),
            type("MockResponse", (), {"content": json.dumps(mock_response)}),
        ]

        # Patch the add_entry (doesn't need to do anything, just avoid real DB write)
        with patch("db.crud.add_entry", new=MagicMock(return_value=True)) as mock_add:
            response = client.post("/generate", json={
                "user_id": user_id,
                "query": query,
                "groq_api_key": "mock key"
            })

            assert response.status_code == 200
            assert "output" in response.json()
            assert response.json()["output"]["casual_response"] == mock_response["casual_response"]

    # Prepare a mock Supabase response for history
    mock_history = [{
        "user_id": user_id,
        "query": query,
        "casual_response": mock_response["casual_response"],
        "formal_response": mock_response["formal_response"],
        "created_at": "2025-01-01T00:00:00"
    }]

    # Patch the supabase client
    with patch("db.crud.supabase") as mock_supabase:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_history
        mock_supabase.table.return_value = mock_table

        history_response = client.get(f"/history?user_id={user_id}")
        assert history_response.status_code == 200
        data = history_response.json()
        assert "output" in data
        assert data["output"][0]["query"] == query
        assert data["output"][0]["casual_response"] == mock_response["casual_response"]
