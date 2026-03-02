import json
from pathlib import Path

import pytest

from backend.models import AppState, User
from backend.state import StateManager


@pytest.fixture
def tmp_state(tmp_path):
    path = tmp_path / "state.json"
    return StateManager(path=path)


def test_read_empty(tmp_state):
    state = tmp_state.read()
    assert isinstance(state, AppState)
    assert state.users == {}


def test_write_and_read(tmp_state):
    state = AppState()
    user = User(name="Tomek", phone="+447123456789", email="tomek@example.com")
    state.users[user.id] = user
    tmp_state.write(state)

    loaded = tmp_state.read()
    assert user.id in loaded.users
    assert loaded.users[user.id].name == "Tomek"


def test_write_creates_backup(tmp_state):
    state1 = AppState()
    user1 = User(name="First", phone="+441111111111", email="first@example.com")
    state1.users[user1.id] = user1
    tmp_state.write(state1)

    state2 = AppState()
    user2 = User(name="Second", phone="+442222222222", email="second@example.com")
    state2.users[user2.id] = user2
    tmp_state.write(state2)

    backup_path = tmp_state.path.with_name("state.backup.json")
    assert backup_path.exists()
    backup_data = json.loads(backup_path.read_text())
    backup_state = AppState.model_validate(backup_data)
    assert user1.id in backup_state.users


def test_update_atomic(tmp_state):
    state = AppState()
    user = User(name="Tomek", phone="+447123456789", email="tomek@example.com")
    state.users[user.id] = user
    tmp_state.write(state)

    def add_credits(s: AppState) -> AppState:
        s.users[user.id].credits += 10
        return s

    new_state = tmp_state.update(add_credits)
    assert new_state.users[user.id].credits == 34

    loaded = tmp_state.read()
    assert loaded.users[user.id].credits == 34


def test_write_atomic_on_failure(tmp_state):
    state = AppState()
    tmp_state.write(state)

    def bad_fn(s: AppState) -> AppState:
        raise ValueError("intentional error")

    with pytest.raises(ValueError):
        tmp_state.update(bad_fn)

    # Original state should be intact
    loaded = tmp_state.read()
    assert loaded.users == {}
