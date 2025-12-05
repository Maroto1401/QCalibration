from pydantic import BaseModel

class PaymentIntent(BaseModel):
    amount: int
    currency: str = 'usd'
