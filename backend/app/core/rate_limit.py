from slowapi import Limiter
from slowapi.util import get_remote_address

# Armazenamento em memória: o contador é por processo. Com 1 worker (plano gratuito) é exato;
# com vários workers o limite efetivo seria multiplicado (aí seria preciso Redis).
limiter = Limiter(key_func=get_remote_address)
