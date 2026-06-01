from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.subscriptions.schemas import (
    PlanOut,
    SubscribeRequest,
    SubscriptionOut,
)
from app.modules.subscriptions.service import SubscriptionService
from app.modules.users.schemas import UserOut
from app.shared.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["subscriptions"])


# FR-USR-02 (gói) / FR-ADM-03: Xem 3 gói Free/Pro/Max, đánh dấu gói hiện tại.
@router.get("/plans", response_model=list[PlanOut])
def list_plans(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return SubscriptionService(db).list_plans(user)


# Đăng ký / nâng cấp gói cho chính mình (Lecturer & Student đều dùng).
@router.post("/subscriptions", response_model=UserOut)
def subscribe(
    payload: SubscribeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return SubscriptionService(db).subscribe(user, payload.plan_id)


@router.get("/subscriptions/me", response_model=SubscriptionOut)
def my_subscription(user=Depends(get_current_user)):
    return SubscriptionOut(plan=user.plan)
