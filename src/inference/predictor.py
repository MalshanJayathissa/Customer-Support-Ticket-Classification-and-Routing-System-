
from pathlib import Path

import joblib
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class TicketPredictor:
    """Load the saved ML models and generate ticket predictions."""

    def __init__(self):
        # Locate the project root and saved model artifacts.
        self.project_root = Path(__file__).resolve().parents[2]
        self.models_dir = self.project_root / "models"

        # Select the GPU when available, otherwise use the CPU.
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # Load the saved primary-category model and tokenizer locally.
        self.primary_dir = (
            self.models_dir / "xlmr_primary_weighted" / "final"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.primary_dir),
            local_files_only=True,
        )
        self.primary_model = (
            AutoModelForSequenceClassification.from_pretrained(
                str(self.primary_dir),
                local_files_only=True,
            )
        )
        self.primary_model.to(self.device)
        self.primary_model.eval()

        # Read the saved label mapping rather than hard-coding categories.
        self.id2label = {
            int(index): label
            for index, label
            in self.primary_model.config.id2label.items()
        }

        # Load the trained scikit-learn models.
        self.secondary_presence_model = joblib.load(
            self.models_dir / "secondary_presence_classifier.joblib"
        )
        self.secondary_category_model = joblib.load(
            self.models_dir / "secondary_category_classifier.joblib"
        )
        self.urgency_model = joblib.load(
            self.models_dir / "urgency_classifier.joblib"
        )

    @staticmethod
    def _clean_value(value):
        # Convert missing values to empty strings without changing real text.
        return "" if value is None else str(value)

    def _combined_text(self, ticket):
        # Preserve the exact feature format used to train the sklearn models.
        subject = self._clean_value(ticket.get("subject"))
        channel = self._clean_value(ticket.get("channel"))
        language = self._clean_value(ticket.get("language"))
        text = self._clean_value(ticket.get("text"))

        return (
            f"subject {subject} "
            f"channel {channel} "
            f"language {language} "
            f"text {text}"
        )

    @torch.inference_mode()
    def predict_batch(self, tickets, chunk_size=4):
        """Predict multiple tickets while limiting transformer memory use."""

        # Validate the batch and ensure every ticket has text.
        if not tickets:
            return []

        for index, ticket in enumerate(tickets):
            if not isinstance(ticket, dict):
                raise TypeError(f"Ticket {index} must be a dictionary.")
            if not self._clean_value(ticket.get("text")).strip():
                raise ValueError(f"Ticket {index} must contain non-empty text.")

        # Primary model uses ticket text only, as in its training pipeline.
        ticket_texts = [
            self._clean_value(ticket.get("text")) for ticket in tickets
        ]

        # Secondary and urgency models use the combined feature format.
        combined_texts = [
            self._combined_text(ticket) for ticket in tickets
        ]

        # Predict primary categories in small chunks to limit GPU memory use.
        primary_results = []

        for start in range(0, len(ticket_texts), chunk_size):
            chunk = ticket_texts[start:start + chunk_size]

            # Tokenize using the same maximum sequence length as training.
            inputs = self.tokenizer(
                chunk,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            inputs = {
                name: tensor.to(self.device)
                for name, tensor in inputs.items()
            }

            # Generate logits and confidence scores.
            outputs = self.primary_model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=-1)
            confidences, predicted_ids = probabilities.max(dim=-1)

            # Convert model indices into the saved category names.
            for predicted_id, confidence in zip(
                predicted_ids.cpu().tolist(),
                confidences.cpu().tolist(),
            ):
                primary_results.append({
                    "category": self.id2label[predicted_id],
                    "confidence": round(float(confidence), 4),
                })

        # Detect whether a secondary label should be returned.
        presence_predictions = self.secondary_presence_model.predict(
            combined_texts
        )

        # Classify secondary categories, but only use them when present.
        secondary_predictions = self.secondary_category_model.predict(
            combined_texts
        )

        # Use the trained urgency decision boundary of zero.
        urgency_scores = self.urgency_model.decision_function(
            combined_texts
        )

        # Combine the outputs into internal predictions.
        results = []

        for index, ticket in enumerate(tickets):
            has_secondary = bool(int(presence_predictions[index]))
            urgency_score = float(urgency_scores[index])

            results.append({
                "ticket_id": ticket.get("ticket_id"),
                "category": primary_results[index]["category"],
                "category_confidence": primary_results[index]["confidence"],
                "secondary_category": (
                    str(secondary_predictions[index])
                    if has_secondary
                    else None
                ),
                "is_urgent": urgency_score >= 0.0,
                "urgency_score": round(urgency_score, 4),
            })

        return results

    def predict_one(self, ticket):
        """Predict one ticket using the same batch inference pipeline."""

        # Reuse the batch implementation to keep predictions consistent.
        return self.predict_batch([ticket])[0]