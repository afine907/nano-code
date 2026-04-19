from nano_code.session.models import Message, Session


def test_message_roundtrip():
    m = Message(role="user", content="Hello")
    d = m.to_dict()
    m2 = Message.from_dict(d)
    assert m2.role == m.role
    assert m2.content == m.content
    assert isinstance(m2.timestamp, float)


def test_session_roundtrip():
    s = Session(id="sess-1", user_id="user-1")
    s.add_message("user", "Hello")
    s.add_message("assistant", "Hi there!")
    d = s.to_dict()
    s2 = Session.from_dict(d)
    assert s2.id == s.id
    assert s2.user_id == s.user_id
    assert len(s2.messages) == 2
