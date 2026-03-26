"""Domain value types — eliminates magic strings across the codebase."""

from enum import StrEnum


class ContactStatus(StrEnum):
    ABERTO = "Aberto"
    AGUARDANDO = "Aguardando Cliente"
    RESOLVIDO = "Resolvido"
    CANCELADO = "Cancelado"


class UserRole(StrEnum):
    GESTOR = "Gestor"
    OPERADOR = "Operador"


class ContactType(StrEnum):
    PESSOA = "Pessoa"
    EMPRESA = "Empresa"


ALLOWED_STATUSES = frozenset(ContactStatus)
