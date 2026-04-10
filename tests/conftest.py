"""Pytest configuration and fixtures for activity API tests."""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


# Store the initial state of activities
INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test.
    
    This fixture runs automatically (autouse=True) before each test
    to ensure test isolation with the in-memory activities database.
    """
    # Reset to initial state before test
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    
    yield
    
    # Cleanup after test (optional, but good practice)
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
