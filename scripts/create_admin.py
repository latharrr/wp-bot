"""One-off bootstrap for the single dashboard operator account.

Usage:
    ppvenv/bin/python scripts/create_admin.py <username> <password>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.auth import hash_password  # noqa: E402
from app.repositories.supabase_admin_repository import SupabaseAdminRepository  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: create_admin.py <username> <password>")
        raise SystemExit(1)

    username, password = sys.argv[1], sys.argv[2]
    repo = SupabaseAdminRepository()
    if repo.get_by_username(username):
        print(f"Admin user '{username}' already exists")
        raise SystemExit(1)

    repo.create(username, hash_password(password))
    print(f"Created admin user '{username}'")


if __name__ == "__main__":
    main()
