from fastapi import Request


def get_client_ip(request: Request) -> str:
    """IP del cliente resistente a spoofing detrás de un proxy.

    Toma el valor MÁS A LA DERECHA de `X-Forwarded-For`: ese lo añade el edge de
    confianza (p.ej. Render), mientras que el más a la izquierda lo controla el cliente
    y sería falsificable — confiar en él (o en `--forwarded-allow-ips=*`) permitiría
    rotar la cabecera y evadir el rate limiting. Sin XFF, cae al peer TCP.

    Nota: la posición exacta depende de cuántos hops agregue el proxy; si Render
    insertara un hop interno adicional, conviene ajustar el índice tras inspeccionar
    el `X-Forwarded-For` real en producción. Por defecto es fail-closed (sobre-limita)
    en vez de fail-open (bypass).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        candidates = [part.strip() for part in forwarded.split(",") if part.strip()]
        if candidates:
            return candidates[-1]
    return request.client.host if request.client else "unknown"
