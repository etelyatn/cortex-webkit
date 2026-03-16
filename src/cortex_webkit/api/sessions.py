# src/cortex_webkit/api/sessions.py
"""CRUD /api/sessions."""

from fastapi import APIRouter, Depends, HTTPException, Request

from cortex_webkit.auth import verify_token
from cortex_webkit.models.chat import SessionCreate, SessionInfo, SessionListResponse

router = APIRouter()


@router.post("/sessions", response_model=SessionInfo)
async def create_session(
    body: SessionCreate,
    request: Request,
    _=Depends(verify_token),
):
    mgr = request.app.state.session_manager
    session = await mgr.create_session(model=body.model, directive=body.directive)
    return session.info()


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(request: Request, _=Depends(verify_token)):
    mgr = request.app.state.session_manager
    sessions = mgr.list_sessions()
    return SessionListResponse(sessions=sessions)


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, request: Request, _=Depends(verify_token)):
    mgr = request.app.state.session_manager
    session = mgr.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.info()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request, _=Depends(verify_token)):
    mgr = request.app.state.session_manager
    deleted = await mgr.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}
