from app.services.predictor import TicketPredictor


CATEGORY_TO_TEAM = {
    "payment_refund": "Payments & Refunds",
    "ride_trip_issue": "Ride Operations",
    "lost_item": "Lost & Found",
    "order_missing_wrong": "Food Operations",
    "delivery_delay": "Delivery Operations",
    "food_quality": "Restaurant Quality",
    "account_promo": "Account Services",
    "safety_conduct": "Trust & Safety",
    "app_technical": "Tech Support",
    "general_inquiry": "Front-line Support",
    "spam_irrelevant": "Auto-close / Spam Filter",
}


class InferenceService:
    def __init__(self):
        self.predictor = TicketPredictor()
        self.model_version = "xlmr-primary-v1"

    def _adapt_prediction(self, prediction):
        category = prediction["category"]

        return {
            "ticket_id": prediction.get("ticket_id"),
            "category": category,
            "secondary_category": prediction.get("secondary_category"),
            "team": CATEGORY_TO_TEAM.get(
                category,
                "Front-line Support",
            ),
            "is_urgent": bool(
                prediction.get("is_urgent", False)
            ),
            "confidence": float(
                prediction.get("category_confidence", 0.0)
            ),
            "model_version": self.model_version,
        }

    def predict_one(self, ticket):
        if hasattr(ticket, "model_dump"):
            ticket_data = ticket.model_dump()
        elif isinstance(ticket, dict):
            ticket_data = ticket
        else:
            raise TypeError(
                "Ticket must be a Pydantic model or dictionary."
            )

        prediction = self.predictor.predict_one(ticket_data)

        return self._adapt_prediction(prediction)

    def predict_batch(self, tickets):
        ticket_dicts = []

        for ticket in tickets:
            if hasattr(ticket, "model_dump"):
                ticket_dicts.append(ticket.model_dump())
            elif isinstance(ticket, dict):
                ticket_dicts.append(ticket)
            else:
                raise TypeError(
                    "Each ticket must be a Pydantic model or dictionary."
                )

        predictions = self.predictor.predict_batch(ticket_dicts)

        return [
            self._adapt_prediction(prediction)
            for prediction in predictions
        ]