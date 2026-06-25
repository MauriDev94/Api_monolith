class DomainError(ValueError):
    """Violación de un invariante o regla del dominio.

    Hereda de ValueError por compatibilidad (el código que ya captura ValueError la
    sigue atrapando), pero es un tipo ESPECÍFICO: el handler la mapea a 400, mientras
    que un ValueError "pelado" (no esperado, normalmente un bug) cae a 500 en vez de
    disfrazarse de error del cliente.
    """
