from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# User Schemas
class UserBase(BaseModel):
    username: str
    role: str = "storekeeper"

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# Item Schemas
class ItemBase(BaseModel):
    item_code: str
    name: str
    unit: str
    current_stock: int = Field(default=0, ge=0)
    image_url: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = None

class ItemResponse(ItemBase):
    id: int

    class Config:
        from_attributes = True

# RequestDetail Schemas
class RequestDetailBase(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)

class RequestDetailCreate(RequestDetailBase):
    pass

class RequestDetailResponse(RequestDetailBase):
    id: int
    item: Optional[ItemResponse] = None

    class Config:
        from_attributes = True

# Request Schemas
class RequestCreate(BaseModel):
    requester_name: str
    destination: Optional[str] = "Phòng / Đơn vị tiếp nhận"
    reason: Optional[str] = "Phục vụ công tác chuyên môn"
    items: List[RequestDetailCreate]

class RequestStatusUpdate(BaseModel):
    status: str  # pending, approved, exported

class RequestResponse(BaseModel):
    id: int
    requester_name: str
    destination: Optional[str] = None
    reason: Optional[str] = None
    status: str
    created_at: datetime
    pdf_path: Optional[str] = None
    excel_path: Optional[str] = None
    word_path: Optional[str] = None
    exported_at: Optional[datetime] = None
    details: List[RequestDetailResponse] = []

    class Config:
        from_attributes = True

class RequestEditExported(BaseModel):
    requester_name: Optional[str] = None
    destination: Optional[str] = None
    reason: Optional[str] = None

# Transaction Schemas
class TransactionResponse(BaseModel):
    id: int
    request_id: Optional[int] = None
    item_id: int
    type: str
    quantity: int
    timestamp: datetime
    item: Optional[ItemResponse] = None

    class Config:
        from_attributes = True
