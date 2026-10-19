import subprocess
import sys

import pytest

# scripts que acessam o banco (setup_storage só fala com o Storage)
SCRIPT_MODULES = [
    "app.scripts.seed_categories",
    "app.scripts.create_admin",
]


@pytest.mark.parametrize("module", SCRIPT_MODULES)
def test_script_entrypoints_load_all_models(module: str) -> None:
    """Regressão: um script rodando sozinho precisa resolver todos os relacionamentos.

    Roda num processo limpo, onde nenhum router foi importado por acaso."""
    code = f"import {module}; from sqlalchemy.orm import configure_mappers; configure_mappers()"
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stderr
