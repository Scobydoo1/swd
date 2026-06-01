from sqlalchemy.orm import Session

from app.modules.subscriptions import plans as plan_catalog
from app.modules.subscriptions.schemas import PlanOut
from app.modules.users.models import Plan, User
from app.modules.users.repository import UserRepository


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def list_plans(self, user: User) -> list[PlanOut]:
        current = user.plan.value if user else "FREE"
        return [
            PlanOut(
                id=p["id"],
                name=p["name"],
                price=p["price"],
                price_label=p["price_label"],
                tagline=p["tagline"],
                features=p["features"],
                highlight=p.get("highlight", False),
                current=p["id"] == current,
            )
            for p in plan_catalog.PLANS
        ]

    def subscribe(self, user: User, plan: Plan) -> User:
        # Demo: "mua" gói là đổi tier ngay, không qua cổng thanh toán thật.
        return self.users.update_plan(user, plan)
