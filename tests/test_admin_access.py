from app import main


def test_admin_access_requires_matching_credentials(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_USERNAME", "owner")
    monkeypatch.setattr(main, "ADMIN_PASSWORD", "safe-password")
    denied = main.unlock_admin("owner", "wrong-password")
    granted = main.unlock_admin("owner", "safe-password")
    assert denied[-1] == "Invalid administrator credentials."
    assert granted[-1].startswith("**Admin access enabled")


def test_open_admin_mode_unlocks_admin_tabs_without_credentials(monkeypatch):
    monkeypatch.setattr(main, "ADMIN_ACCESS_MODE", "open")
    result = main.apply_user_mode("Admin")
    assert result[-1] == "**Open admin mode enabled for all visitors.**"
