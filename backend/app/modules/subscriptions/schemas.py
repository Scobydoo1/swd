from pydantic import BaseModel

from app.modules.users.models import Plan


class PlanOut(BaseModel):
    id: str
    name: str
    price: int
    price_label: str
    tagline: str
    features: list[str]
    highlight: bool = False
    current: bool = False


class SubscribeRequest(BaseModel):
    plan_id: Plan


class SubscriptionOut(BaseModel):
    plan: Plan
