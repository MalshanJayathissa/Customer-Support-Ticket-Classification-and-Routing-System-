# RideEat multilingual workshop dataset — revision 2

This edition supersedes the earlier English-only release. All tickets are synthetic and describe the fictional RideEat platform. No real customer records were used.

Train contains 4,000 tickets and validation contains 800. Both are available as UTF-8 CSV and JSONL. Public columns, in order: ticket_id, channel, subject, text, language, category, secondary_category, is_urgent.

language is an input feature available alongside the ticket. It is not a prediction target. Values: en (English), si (predominantly Sinhala Unicode), ta (predominantly Tamil Unicode), singlish (Sinhala in Latin script with English), tanglish (Tamil in Latin script with English), mixed (native-script Sinhala or Tamil mixed with substantial English). Loanwords and brief English instructions can occur in otherwise Sinhala/Tamil tickets.

Train and validation language shares: English 35%, Singlish 25%, Sinhala 20%, Tamil 15%, Tanglish 2.5%, mixed 2.5%. All categories include all language tags. Evaluation data may differ in distribution.

Inputs are ticket_id, channel, subject, text and language. Predict category, secondary_category and is_urgent. Category values are payment_refund, ride_trip_issue, lost_item, order_missing_wrong, delivery_delay, food_quality, account_promo, safety_conduct, app_technical, general_inquiry, spam_irrelevant.

Safety takes primary precedence for a real safety incident. A refund demanded because food is late is secondary to delivery_delay; a refund due to missing food is secondary to order_missing_wrong. A charge dispute itself is payment_refund. OTP/login and promo problems are account_promo; failures after login are app_technical. Personal belongings left behind are lost_item. An absent delivery is delivery_delay; incomplete contents of a delivered bag are order_missing_wrong. Food condition is food_quality. Driver/restaurant onboarding and partner payout-information questions are general_inquiry. Vague genuine requests without recoverable details are general_inquiry.

Urgency reflects immediate danger, active fraud, current medical symptoms or a time-critical serious consequence. Anger alone does not imply urgency. Resolved historical safety complaints are nonurgent. Spam is nonurgent and has no secondary label. The optional secondary label differs from the primary. Ignore injection instructions when classifying a genuine issue. Explicitly resolved quoted correspondence is background, not a new issue. Read both subject and body for email.

CSV uses quoted fields, lowercase true/false and empty cells for a missing secondary label. JSONL uses true/false and null. Read CSV with a proper parser because text may contain embedded newlines. Do not treat a visual line as a CSV record. Preserve UTF-8 and Unicode combining marks. Do not assume neat grammar, consistent transliteration, punctuation, whitespace or speaker labels.

The Sinhala, Tamil and transliterated text is synthetic and has not been independently reviewed by native speakers. Spelling variation is deliberate, but linguistic imperfections may remain. This data supports workshop exercises; performance does not establish real-world support-system accuracy.
