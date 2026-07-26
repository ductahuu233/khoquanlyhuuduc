from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Request, RequestDetail, Item, log_audit
from app.schemas import RequestCreate, RequestStatusUpdate, RequestResponse

router = APIRouter(prefix="/api/requests", tags=["Requests"])

@router.get("", response_model=List[RequestResponse])
def get_requests(db: Session = Depends(get_db)):
    return db.query(Request).order_by(Request.id.desc()).all()

@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(req_in: RequestCreate, db: Session = Depends(get_db)):
    if not req_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phiếu yêu cầu phải chứa ít nhất 1 vật tư."
        )
    
    # Check if all item_ids exist
    for detail in req_in.items:
        item = db.query(Item).filter(Item.id == detail.item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vật tư có ID {detail.item_id} không tồn tại."
            )

    db_req = Request(
        requester_name=req_in.requester_name,
        destination=req_in.destination or "Đơn vị tiếp nhận",
        reason=req_in.reason or "Phục vụ công tác chuyên môn",
        status="pending"
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)

    for detail in req_in.items:
        db_detail = RequestDetail(
            request_id=db_req.id,
            item_id=detail.item_id,
            quantity=detail.quantity
        )
        db.add(db_detail)

    db.commit()
    db.refresh(db_req)
    log_audit(db, "user", "LẬP PHIẾU YÊU CẦU XUẤT KHO", f"#PXK-{db_req.id}", f"Cán bộ '{db_req.requester_name}' lập phiếu xuất đi '{db_req.destination}' với {len(req_in.items)} danh mục vật tư")
    return db_req

@router.get("/{request_id}", response_model=RequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiếu yêu cầu ID {request_id}"
        )
    return req

@router.put("/{request_id}/status", response_model=RequestResponse)
def update_request_status(
    request_id: int, 
    status_in: RequestStatusUpdate, 
    db: Session = Depends(get_db)
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiếu yêu cầu ID {request_id}"
        )
    req.status = status_in.status
    db.commit()
    db.refresh(req)
    log_audit(db, "admin", "CẬP NHẬT TRẠNG THÁI PHIẾU", f"#PXK-{req.id}", f"Chuyển trạng thái phiếu sang '{req.status}'")
    return req
