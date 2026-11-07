"""Q03：受认证保护的流水线实验；不创建会话或保存消息。"""

from fastapi import APIRouter, Depends
from ..dependencies import current_user
from ...models import User
from ...schemas.chain import ChainInput, ChainReport
from ...services.chain import run_experiment

router = APIRouter(prefix="/chains", tags=["Runnable 实验"])


@router.post("/inspect", response_model=ChainReport)
def inspect(body: ChainInput, user: User = Depends(current_user)):
    return run_experiment(body, inspect=True)


@router.post("/run", response_model=ChainReport)
def run(body: ChainInput, user: User = Depends(current_user)):
    return run_experiment(body)
