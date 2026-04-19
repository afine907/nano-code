from nano_code.session.manager import SessionManager


def test_create_and_save_session(tmp_path):
    storage = str(tmp_path)
    sm = SessionManager(storage_dir=storage)
    s = sm.create_session(user_id="user-1")
    sm.add_message(s.id, "user", "Hello world")
    # simulate restart by creating a new manager pointing to same storage
    sm2 = SessionManager(storage_dir=storage)
    s2 = sm2.get_session(s.id)
    assert s2 is not None
    assert s2.id == s.id
    assert len(s2.messages) == 1


def test_recover_session(tmp_path):
    storage = str(tmp_path)
    sm = SessionManager(storage_dir=storage)
    s = sm.create_session()
    sm.add_message(s.id, "user", "first message")
    recovered = sm.recover_session(s.id)
    assert recovered is not None
    assert len(recovered.messages) == 1
    assert recovered.messages[0].content == "first message"
