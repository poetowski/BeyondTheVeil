import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.campaign import CampaignChapterOut, CampaignNodeOut, to_chapter_out, to_out
from app.schemas.veil_run import VeilRunOut
from app.schemas.veil_run import to_out as veil_run_to_out
from app.services import campaign_service

router = APIRouter(prefix="/campaign", tags=["campaign"])


@router.get("/chapters", response_model=list[CampaignChapterOut])
def get_campaign_chapters(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CampaignChapterOut]:
    chapters = campaign_service.list_chapters(db)
    return [to_chapter_out(chapter) for chapter in chapters]


@router.get("/nodes", response_model=list[CampaignNodeOut])
def get_campaign_nodes(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CampaignNodeOut]:
    nodes = campaign_service.list_nodes(db)
    return [to_out(node, current_user.hero) for node in nodes]


@router.post("/nodes/{node_id}/enter", response_model=VeilRunOut)
def enter_campaign_node(
    node_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VeilRunOut:
    try:
        run = campaign_service.enter_campaign_node(db, current_user.hero, node_id)
    except campaign_service.NodeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except campaign_service.CampaignError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return veil_run_to_out(run)
