from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EmpresaItem(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(populate_by_name=True)


class EmpresasListaResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None
    empresas: List[EmpresaItem] = []
    total: int = 0

    model_config = ConfigDict(populate_by_name=True)
