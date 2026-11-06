"""Explicit database and account operations. No credentials are built in."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init-db")
    init.add_argument("--seed-demo", action="store_true")
    backup = commands.add_parser("backup")
    backup.add_argument("--source", required=True)
    backup.add_argument("--output-dir", required=True)
    verify = commands.add_parser("verify-backup")
    verify.add_argument("backup")
    restore = commands.add_parser("restore")
    restore.add_argument("backup")
    restore.add_argument("--target", required=True)
    restore.add_argument("--replace", action="store_true")
    user = commands.add_parser("create-user")
    user.add_argument("--username", required=True)
    user.add_argument(
        "--role", choices=["admin", "dosen", "penjamin_mutu"], required=True
    )
    user.add_argument("--course-id", action="append", default=[])
    args = parser.parse_args()
    from app.core.recovery import backup_database, verify_backup, restore_database

    if args.command == "init-db":
        from app.core.database import init_db
        from app.core.database import engine
        from app.core.recovery import DatabaseLease

        path = Path(engine.url.database).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with DatabaseLease(path):
            init_db(allow_create=True, seed_demo=args.seed_demo)
        print("Database siap; akun harus dibuat secara eksplisit.")
    elif args.command == "create-user":
        import os
        from getpass import getpass
        from app.core.database import init_db, SessionLocal, engine
        from app.core.auth import create_user
        from app.models.security import CourseAccess
        from app.models.course import Course
        from app.core.audit import record
        from types import SimpleNamespace
        from app.core.recovery import DatabaseLease

        password = os.getenv("EDUCOPILOT_ACCOUNT_PASSWORD") or getpass(
            "Password baru (minimal 12 karakter): "
        )
        with DatabaseLease(engine.url.database):
            init_db()
            with SessionLocal() as db:
                if args.course_id and args.role != "dosen":
                    raise ValueError("Penugasan hanya untuk dosen.")
                for cid in args.course_id:
                    if not db.get(Course, cid):
                        raise ValueError("Mata kuliah tidak ditemukan: " + cid)
                account = create_user(db, args.username, password, args.role)
                for cid in set(args.course_id):
                    db.add(CourseAccess(user_id=account.id, course_id=cid))
                record(
                    db,
                    "account_create",
                    "users",
                    account.id,
                    actor=SimpleNamespace(
                        id=None, username="operator-cli", role="operator"
                    ),
                )
                db.commit()
                print(
                    json.dumps(
                        {
                            "id": account.id,
                            "username": account.username,
                            "role": account.role,
                        }
                    )
                )
    elif args.command == "backup":
        print(backup_database(args.source, args.output_dir))
    elif args.command == "verify-backup":
        print(json.dumps(verify_backup(args.backup), indent=2))
    elif args.command == "restore":
        print(
            json.dumps(
                restore_database(args.backup, args.target, replace=args.replace),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
