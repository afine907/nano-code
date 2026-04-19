"""会话管理器测试"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from nano_code.cli.session_manager import Session, SessionManager


class TestSession:
    """测试 Session 数据类"""

    def test_basic_creation(self):
        """测试基本创建"""
        session = Session(id="test123", name="Test Session")
        assert session.id == "test123"
        assert session.name == "Test Session"
        assert session.message_count == 0
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_full_creation(self):
        """测试完整创建"""
        created = datetime.now()
        updated = datetime.now()
        storage_path = Path("/tmp/test.json")
        session = Session(
            id="test456",
            name="Full Session",
            created_at=created,
            updated_at=updated,
            message_count=5,
            storage_path=storage_path,
        )
        assert session.id == "test456"
        assert session.name == "Full Session"
        assert session.created_at == created
        assert session.updated_at == updated
        assert session.message_count == 5
        assert session.storage_path == storage_path

    def test_to_dict(self):
        """测试转换为字典"""
        session = Session(id="test789", name="Dict Session", message_count=3)
        data = session.to_dict()
        assert data["id"] == "test789"
        assert data["name"] == "Dict Session"
        assert data["message_count"] == 3
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "from_dict",
            "name": "From Dict Session",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
            "message_count": 10,
        }
        session = Session.from_dict(data)
        assert session.id == "from_dict"
        assert session.name == "From Dict Session"
        assert session.message_count == 10


class TestSessionManager:
    """测试 SessionManager 类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """创建 SessionManager 实例"""
        return SessionManager(sessions_dir=temp_dir)

    def test_initialization(self, manager, temp_dir):
        """测试初始化"""
        assert manager.sessions_dir == temp_dir
        assert manager._current_session_id is None
        assert len(manager._sessions) == 0

    def test_create_session(self, manager):
        """测试创建会话"""
        session = manager.create_session("Test Session")
        assert session.id is not None
        assert session.name == "Test Session"
        assert session.storage_path is not None
        assert session.id in manager._sessions

    def test_create_session_default_name(self, manager):
        """测试创建会话使用默认名称"""
        session = manager.create_session()
        assert session.name is not None
        assert "会话" in session.name

    def test_get_session(self, manager):
        """测试获取会话"""
        session = manager.create_session("Get Test")
        retrieved = manager.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id

    def test_get_nonexistent_session(self, manager):
        """测试获取不存在的会话"""
        result = manager.get_session("nonexistent")
        assert result is None

    def test_switch_session(self, manager):
        """测试切换会话"""
        session1 = manager.create_session("Session 1")
        _session2 = manager.create_session("Session 2")
        result = manager.switch_session(session1.id)
        assert result is True
        assert manager._current_session_id == session1.id

    def test_switch_nonexistent_session(self, manager):
        """测试切换不存在的会话"""
        result = manager.switch_session("nonexistent")
        assert result is False

    def test_delete_session(self, manager):
        """测试删除会话"""
        session = manager.create_session("Delete Test")
        session_id = session.id
        result = manager.delete_session(session_id)
        assert result is True
        assert session_id not in manager._sessions

    def test_delete_nonexistent_session(self, manager):
        """测试删除不存在的会话"""
        result = manager.delete_session("nonexistent")
        assert result is False

    def test_list_sessions(self, manager):
        """测试列出所有会话"""
        session1 = manager.create_session("Session 1")
        session2 = manager.create_session("Session 2")
        sessions = manager.list_sessions()
        assert len(sessions) == 2
        assert sessions[0].id in [session1.id, session2.id]

    def test_get_current_session(self, manager):
        """测试获取当前会话"""
        session = manager.create_session("Current Test")
        current = manager.get_current_session()
        assert current is not None
        assert current.id == session.id

    def test_get_current_session_none(self, manager):
        """测试获取当前会话（无当前会话）"""
        manager._current_session_id = None
        current = manager.get_current_session()
        assert current is None

    def test_get_or_create_current_session(self, manager):
        """测试获取或创建当前会话"""
        session = manager.get_or_create_current_session()
        assert session is not None

    def test_get_or_create_current_session_creates_new(self, manager):
        """测试获取或创建当前会话（无会话时创建新会话）"""
        session1 = manager.create_session("First Session")
        assert manager._current_session_id == session1.id
        session2 = manager.get_or_create_current_session()
        assert session2.id == session1.id

    def test_update_session_activity(self, manager):
        """测试更新会话活动"""
        session = manager.create_session("Activity Test")
        original_updated = session.updated_at
        manager.update_session_activity(session.id)
        assert session.updated_at > original_updated

    def test_persistence(self, temp_dir):
        """测试会话持久化"""
        manager1 = SessionManager(sessions_dir=temp_dir)
        session = manager1.create_session("Persist Test")
        session_id = session.id
        index_file = temp_dir / "index.json"
        assert index_file.exists()
        with open(index_file) as f:
            data = json.load(f)
        assert session_id in [s["id"] for s in data["sessions"]]
        assert data["current_session_id"] == session_id

        manager2 = SessionManager(sessions_dir=temp_dir)
        assert manager2._current_session_id == session_id
        assert session_id in manager2._sessions

    def test_delete_session_removes_storage_file(self, manager):
        """测试删除会话时删除存储文件"""
        session = manager.create_session("Storage Test")
        storage_path = session.storage_path
        if storage_path:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            storage_path.write_text("test content")
            assert storage_path.exists()
        manager.delete_session(session.id)
        if storage_path:
            assert not storage_path.exists()

    def test_switch_after_delete(self, manager):
        """测试删除当前会话后切换"""
        session1 = manager.create_session("Session 1")
        _session2 = manager.create_session("Session 2")
        manager.switch_session(session1.id)
        manager.delete_session(session1.id)
        assert manager._current_session_id is None

    def test_multiple_sessions_independence(self, manager):
        """测试多个会话相互独立"""
        session1 = manager.create_session("Independent 1")
        session2 = manager.create_session("Independent 2")
        assert session1.id != session2.id
        assert session1.id in manager._sessions
        assert session2.id in manager._sessions
        assert manager._current_session_id == session2.id
