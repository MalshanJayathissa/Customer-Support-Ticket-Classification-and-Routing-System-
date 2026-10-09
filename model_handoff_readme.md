ML Model Artifacts

This directory contains the trained machine learning models used by the Customer Support Ticket Classification and Routing System.

Model Files

The model artifacts are excluded from Git because of their size. The final inference artifacts are packaged separately in model_handoff.zip.

1. Primary Category Classifier

Directory: xlmr_primary_weighted/final/
Model: XLM-RoBERTa Base, class-weighted fine-tuning
Task: Classifies a support ticket into one of 11 primary categories.

Supported categories:

account_promo
app_technical
delivery_delay
food_quality
general_inquiry
lost_item
order_missing_wrong
payment_refund
ride_trip_issue
safety_conduct
spam_irrelevant

The model directory includes the model weights, tokenizer, and configuration files.

2. Secondary-Label Presence Classifier

File: secondary_presence_classifier.joblib
Model type: Character TF-IDF with Linear SVM
Task: Predicts whether a ticket should receive a secondary category label.

3. Secondary Category Classifier

File: secondary_category_classifier.joblib
Model type: Character TF-IDF with Linear SVM
Task: Predicts the secondary category when a secondary label is present.

Supported secondary categories:

app_technical
delivery_delay
order_missing_wrong
payment_refund
ride_trip_issue
4. Urgency Classifier

File: urgency_classifier.joblib
Model type: Character TF-IDF with Linear SVM
Task: Classifies whether a ticket is urgent.

Obtaining the Artifacts

The model artifacts are not committed to the Git repository.

Obtain model_handoff.zip from the project team's shared storage. Extract its contents and place the files in the directory structure expected by src/inference/predictor.py and the API integration.

The handoff archive contains:

The final weighted XLM-RoBERTa model and tokenizer/configuration files.
The secondary-label presence classifier.
The secondary category classifier.
The urgency classifier.
Inference Notes
The primary classifier uses the ticket text.
The secondary-label and urgency classifiers use the combined subject, channel, language, and text representation.
The primary model and tokenizer must load from local files; runtime internet access should not be required.
Verify the model paths and run an inference test after extracting the artifacts.