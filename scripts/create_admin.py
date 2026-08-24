"""One-off bootstrap for the super admin account. This is the only user created outside the
dashboard -- the super admin then creates every other ('user'-role) account from the Admin page,
choosing which features each one can see.

Usage:
    .venv/bin/python scripts/create_admin.py <username> <password>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.auth import hash_password
from app.repositories.supabase_admin_repository import (
    SupabaseAdminRepository,
)


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: create_admin.py <username> <password>")
        raise SystemExit(1)

    username, password = sys.argv[1], sys.argv[2]
    repo = SupabaseAdminRepository()
    if repo.get_by_username(username):
        print(f"User '{username}' already exists")
        raise SystemExit(1)

    repo.create(username, hash_password(password), role="super_admin")
    print(f"Created super admin '{username}'")


if __name__ == "__main__":
    main()
