"""Cria um administrador. Uso: python -m app.scripts.create_admin --email pessoa@exemplo.com

A senha é pedida no terminal (não aparece na tela nem fica no histórico do shell).
"""

import argparse
import getpass
import sys

import app.models  # noqa: F401  (registra todos os models)
from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.modules.admins import service


def main() -> int:
    parser = argparse.ArgumentParser(description="Cria um administrador do painel.")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Senha: ")
    if password != getpass.getpass("Confirme a senha: "):
        print("As senhas não coincidem.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            admin = service.create_admin(db, args.email, password)
        except AppError as exc:
            print(f"Erro: {exc.message}", file=sys.stderr)
            return 1
    print(f"Administrador criado: {admin.email} (id {admin.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
