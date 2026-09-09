"""Criação explícita de administrador, usando senha digitada no terminal."""

import argparse
from getpass import getpass
import sqlite3

from .auth import hash_password
from .config import Config
from .database import Database
from .rules import validate_username


def main():
    parser = argparse.ArgumentParser(description="Criar administrador do Ponto Facial")
    parser.add_argument("usuario")
    parser.add_argument("--nome", default="Administrador")
    args = parser.parse_args()
    try:
        username = validate_username(args.usuario)
        database = Database(Config.from_env().data_dir)
        if database.user(username):
            raise ValueError("Usuário já existe; nenhuma senha foi alterada.")
        password = getpass("Senha (mínimo 12 caracteres): ")
        if password != getpass("Confirme a senha: "):
            raise ValueError("As senhas não coincidem.")
        database.add_user(args.nome, username, hash_password(password), "admin")
    except (ValueError, sqlite3.IntegrityError) as error:
        parser.exit(1, f"Erro: {error}\n")
    print("Administrador criado. A senha não será exibida.")


if __name__ == "__main__":
    main()
