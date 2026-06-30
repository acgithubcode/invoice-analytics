from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, manager_or_admin
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.services.client_service import (
    create_client,
    delete_client,
    get_client_by_gstin,
    get_client_by_id,
    list_clients,
    update_client,
)

router = APIRouter()


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_new_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> Client:
    existing_client = get_client_by_gstin(db, payload.gstin)
    if existing_client:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GSTIN is already registered.")
    return create_client(db, payload, current_user)


@router.get("", response_model=list[ClientRead])
def read_clients(
    search: str | None = Query(default=None, description="Search by client name."),
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[Client]:
    return list_clients(db, search)


@router.get("/{client_id}", response_model=ClientRead)
def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> Client:
    client = get_client_by_id(db, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


@router.put("/{client_id}", response_model=ClientRead)
def update_existing_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> Client:
    client = get_client_by_id(db, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    existing_client = get_client_by_gstin(db, payload.gstin)
    if existing_client and existing_client.id != client.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GSTIN is already registered.")

    return update_client(db, client, payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(manager_or_admin)])
def delete_existing_client(client_id: int, db: Session = Depends(get_db)) -> Response:
    client = get_client_by_id(db, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    delete_client(db, client)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
