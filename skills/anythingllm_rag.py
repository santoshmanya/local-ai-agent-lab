#!/usr/bin/env python3
"""
AnythingLLM RAG Integration for Vedic Astro Guru
Queries the local AnythingLLM instance for Vedic wisdom from PDFs
"""

import os
import requests
from typing import Optional

# AnythingLLM Configuration
ANYTHINGLLM_BASE_URL = os.getenv("ANYTHINGLLM_BASE_URL", "http://localhost:3001")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "")  # Optional for local
ANYTHINGLLM_WORKSPACE = os.getenv("ANYTHINGLLM_WORKSPACE", "vedic-wisdom")


def query_vedic_knowledge(question: str, workspace: Optional[str] = None) -> dict:
    """
    Query AnythingLLM for Vedic wisdom based on ingested PDFs.
    
    Args:
        question: The question to ask about Vedic scriptures
        workspace: Optional workspace name (defaults to vedic-wisdom)
    
    Returns:
        dict with 'answer' and 'sources'
    """
    workspace = workspace or ANYTHINGLLM_WORKSPACE
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if ANYTHINGLLM_API_KEY:
        headers["Authorization"] = f"Bearer {ANYTHINGLLM_API_KEY}"
    
    # AnythingLLM chat endpoint
    url = f"{ANYTHINGLLM_BASE_URL}/api/v1/workspace/{workspace}/chat"
    
    payload = {
        "message": question,
        "mode": "query"  # Use 'query' for RAG, 'chat' for conversation
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return {
            "answer": data.get("textResponse", ""),
            "sources": data.get("sources", []),
            "success": True
        }
    except requests.exceptions.RequestException as e:
        return {
            "answer": f"Error querying Vedic knowledge: {str(e)}",
            "sources": [],
            "success": False
        }


def list_workspaces() -> list:
    """List all available workspaces in AnythingLLM"""
    headers = {"Accept": "application/json"}
    if ANYTHINGLLM_API_KEY:
        headers["Authorization"] = f"Bearer {ANYTHINGLLM_API_KEY}"
    
    try:
        response = requests.get(
            f"{ANYTHINGLLM_BASE_URL}/api/v1/workspaces",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("workspaces", [])
    except requests.exceptions.RequestException as e:
        print(f"Error listing workspaces: {e}")
        return []


def get_workspace_documents(workspace: str) -> list:
    """Get documents in a workspace"""
    headers = {"Accept": "application/json"}
    if ANYTHINGLLM_API_KEY:
        headers["Authorization"] = f"Bearer {ANYTHINGLLM_API_KEY}"
    
    try:
        response = requests.get(
            f"{ANYTHINGLLM_BASE_URL}/api/v1/workspace/{workspace}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("workspace", {}).get("documents", [])
    except requests.exceptions.RequestException as e:
        print(f"Error getting documents: {e}")
        return []


# Example Vedic wisdom queries
SAMPLE_QUERIES = [
    "What does the Bhagavad Gita say about karma?",
    "How should one deal with anger according to Vedas?",
    "What is the meaning of dharma in Hindu scriptures?",
    "What does Kama Sutra say about love and relationships?",
    "How to find peace according to Upanishads?",
    "What is the significance of birth stars in Vedic astrology?",
]


if __name__ == "__main__":
    print("=" * 60)
    print("AnythingLLM Vedic Wisdom RAG Test")
    print("=" * 60)
    
    # Test connection
    print(f"\n[CONFIG] Base URL: {ANYTHINGLLM_BASE_URL}")
    print(f"[CONFIG] Workspace: {ANYTHINGLLM_WORKSPACE}")
    
    # List workspaces
    print("\n[TEST] Listing workspaces...")
    workspaces = list_workspaces()
    if workspaces:
        print(f"[OK] Found {len(workspaces)} workspace(s):")
        for ws in workspaces:
            print(f"  - {ws.get('name', 'Unknown')}")
    else:
        print("[WARN] No workspaces found or connection failed")
    
    # Test query
    print("\n[TEST] Querying Vedic knowledge...")
    test_question = "What does the Bhagavad Gita say about dealing with difficult times?"
    result = query_vedic_knowledge(test_question)
    
    if result["success"]:
        print(f"\n[Q] {test_question}")
        print(f"\n[A] {result['answer'][:500]}...")
        if result["sources"]:
            print(f"\n[Sources] {len(result['sources'])} document(s) referenced")
    else:
        print(f"[ERROR] {result['answer']}")
    
    print("\n" + "=" * 60)
