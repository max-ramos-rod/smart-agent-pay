# utils/idempotency.py — versão corrigida
# Problema original: hash só de strategy_id+price → colide se preço repetir
# Correção: inclui timestamp truncado em janela de 5s para evitar colisões
# mas ainda bloquear duplicatas dentro da mesma janela de execução

import hashlib
from datetime import datetime, timezone

def generate_execution_id(strategy_id: int, price: float) -> str:
    # Janela de 5s: execuções do mesmo agente no mesmo preço dentro de 5s = duplicata
    window = int(datetime.now(timezone.utc).timestamp() // 5)
    raw = f"{strategy_id}:{round(price, 2)}:{window}"
    return hashlib.sha256(raw.encode()).hexdigest()
