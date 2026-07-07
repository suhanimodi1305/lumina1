# Requirements Document

## Introduction

This feature adds a Traya-style hair care consultation and onboarding flow to the Lumina Django application. When a new user registers (or an existing user has not yet completed the consultation), the system presents a multi-step animated quiz that gathers information about hair concerns, scalp condition, lifestyle, diet, stress level, and health history. Based on quiz answers, a recommendation engine maps responses to relevant hair care products already in the catalogue (product_range = 'ayurvedic', 'pharmacy', or 'treatment'). After the consultation, the system sends follow-up messages via SMS and WhatsApp to remind the user of their personalised plan and encourage engagement. The entire flow uses engaging animations, progress indicators, and a visually appealing card-based UI consistent with the Lumina design system.

---

## Glossary

- **Consultation**: The multi-step hair care quiz a user completes to receive personalised product recommendations.
- **ConsultationSession**: A database record that stores a user's quiz answers, completion status, and timestamp for a single consultation attempt.
- **ConsultationAnswer**: A per-question answer stored against a ConsultationSession.
- **QuizQuestion**: A predefined question in the hair care quiz (question text, question type, options list, and the topic category it belongs to).
- **RecommendationEngine**: The rule-based component that maps ConsultationAnswer combinations to Product records.
- **HairRecommendation**: A record linking a ConsultationSession to one or more recommended Products, with an explanation note.
- **MessagingService**: The component responsible for dispatching SMS and WhatsApp messages via an external provider (e.g., Twilio or Fast2SMS).
- **OutboundMessage**: A log record for every SMS or WhatsApp message dispatched, including delivery status.
- **Lumina_System**: The overall Django web application (used as the system name in EARS requirements).
- **Quiz_UI**: The animated frontend layer that renders quiz steps, progress bars, and answer cards.
- **Recommendation_Engine**: Synonym for RecommendationEngine when used in EARS statements.
- **Messaging_Service**: Synonym for MessagingService when used in EARS statements.
- **User**: An authenticated Django `auth.User` record.
- **Hair_Profile**: The aggregated, human-readable summary derived from a completed ConsultationSession (stored as JSON on the session record).

---

## Requirements

### Requirement 1: Hair Care Consultation Quiz Entry Point

**User Story:** As a new user, I want to be guided into a hair care consultation quiz immediately after signup, so that I can receive personalised product recommendations from the start.

#### Acceptance Criteria

1. WHEN a User completes signup, THE Lumina_System SHALL redirect the User to the consultation quiz start page before showing the main dashboard.
2. WHEN an authenticated User visits the main dashboard, THE Lumina_System SHALL display a banner in the top section of the dashboard content area, above all other content, containing a call-to-action linking to the consultation quiz.
3. WHEN an authenticated User who has already completed a ConsultationSession logs in, THE Lumina_System SHALL NOT redirect the User to the quiz automatically, but SHALL still display the quiz banner on the dashboard.
4. IF an authenticated User has persistently dismissed the quiz banner 3 or more times across all sessions without completing a ConsultationSession, THEN THE Lumina_System SHALL suppress the quiz banner and instead display a "Retake Quiz" link exclusively within the user profile section.
5. WHEN an authenticated User selects the pause option during the consultation quiz, THE Lumina_System SHALL save all answers entered up to that point and confirm to the User that progress has been saved before exiting the quiz.
6. WHEN an authenticated User resumes a previously paused ConsultationSession, THE Lumina_System SHALL restore all previously saved answers and return the User to the first unanswered question.
7. IF saving quiz progress fails, THEN THE Lumina_System SHALL display an error message indicating that progress could not be saved and SHALL keep the User on the current quiz page without discarding any entered answers.

---

### Requirement 2: Multi-Step Animated Quiz Flow

**User Story:** As a user, I want to answer quiz questions in a visually engaging step-by-step interface, so that the consultation feels approachable and easy to complete.

#### Acceptance Criteria

1. THE Quiz_UI SHALL present each quiz question on a full-screen card with a visible animated progress bar showing the exact calculated percentage of questions answered (questions_answered / total_questions × 100).
2. WHEN a User selects an answer option, THE Quiz_UI SHALL animate the transition to the next question within 400 milliseconds using a slide or fade animation.
3. THE Quiz_UI SHALL support four question types: single-choice (radio), multi-choice (checkbox), scale (1–5 slider), and free-text (textarea, max 300 characters).
4. IF a User attempts to proceed past a question marked with a required indicator without providing an answer, THEN THE Quiz_UI SHALL display an inline validation message adjacent to the unanswered question and prevent navigation to the next step.
5. THE Quiz_UI SHALL display a step counter (e.g., "Question 3 of 15") and a back button on every step except the first.
6. WHEN the User reaches the final question and submits, THE Quiz_UI SHALL show an animated "Analysing your hair profile…" loader screen for at least 1.5 seconds and no more than 5 seconds before displaying results.
7. THE Quiz_UI SHALL be fully responsive such that: (a) no horizontal scrollbar appears, (b) all text remains legible without zooming, (c) all interactive elements are reachable by touch or click, and (d) no content is clipped or hidden on screen widths from 320 px to 1920 px.
8. WHEN a User navigates back to a previously answered question, THE Quiz_UI SHALL restore the User's previously selected answer for that question.

---

### Requirement 3: Quiz Question Bank

**User Story:** As a product manager, I want a configurable set of questions covering all key hair health dimensions, so that the recommendation engine has enough signal to produce relevant suggestions.

#### Acceptance Criteria

1. THE Lumina_System SHALL store at minimum 15 QuizQuestion records covering the following topic categories: hair_concern, hair_type, scalp_condition, hair_loss_duration, diet, water_intake, sleep, stress_level, physical_activity, medical_history, previous_treatments, age_group, gender, water_type, and hair_wash_frequency.
2. THE Lumina_System SHALL allow Django admin users to add, edit, deactivate, and reorder QuizQuestion records without code deployment.
3. WHEN a QuizQuestion is marked inactive, THE Lumina_System SHALL exclude it from all new ConsultationSessions while preserving existing ConsultationAnswer records that referenced it; IF an admin attempts to permanently delete a QuizQuestion that has at least one associated ConsultationAnswer, THEN THE Lumina_System SHALL reject the deletion and display a message stating that the question has associated answers.
4. THE Lumina_System SHALL enforce that each QuizQuestion has a non-empty question_text, a question_type value that is one of `single_choice`, `multi_choice`, `scale`, or `free_text`, and at least one option defined for `single_choice` and `multi_choice` types; no option validation is required for `scale` and `free_text` types.
5. WHERE a QuizQuestion has `is_required = True`, THE Lumina_System SHALL prevent ConsultationSession submission until that question has a saved ConsultationAnswer containing a non-blank response; WHEN the User attempts to submit with a missing required answer, THE Lumina_System SHALL display an error identifying which required questions remain unanswered and SHALL NOT allow "prefer not to answer" as a substitute.

---

### Requirement 4: Answer Storage and Hair Profile Generation

**User Story:** As a developer, I want quiz answers stored persistently and a structured hair profile derived from them, so that recommendations can be recalculated and audited at any time.

#### Acceptance Criteria

1. WHEN a User submits a ConsultationSession, THE Lumina_System SHALL atomically persist all ConsultationAnswer records linked to that session (all records saved or none saved) in the database within 2 seconds.
2. WHEN a ConsultationSession is marked complete, THE Lumina_System SHALL compute a Hair_Profile JSON object from the answers within 5 seconds and store it on the ConsultationSession record, where "complete answers" means all required QuizQuestion records have a corresponding ConsultationAnswer with a non-null, non-empty response value.
3. IF Hair_Profile computation fails because one or more required answers are missing or contain invalid values, THEN THE Lumina_System SHALL prevent the session from being marked complete and return an error message identifying which specific answers are missing or invalid.
4. WHEN a User initiates a new quiz attempt while a previous ConsultationSession exists, THE Lumina_System SHALL create a new ConsultationSession and preserve all ConsultationAnswer records from the previous session without modification.
5. IF a ConsultationSession save operation fails due to a database error, THEN THE Lumina_System SHALL roll back all changes from that save operation, return an HTTP 500 response with a message indicating what failed and that the User's progress was not saved, and log the exception to the application error log.
6. THE Lumina_System SHALL expose a read-only view in Django admin showing ConsultationSession records with their computed Hair_Profile and associated ConsultationAnswer list for each User.

---

### Requirement 5: Product Recommendation Engine

**User Story:** As a user, I want to receive personalised hair care product suggestions based on my quiz answers, so that I know exactly which products to use for my specific hair concerns.

#### Acceptance Criteria

1. WHEN a ConsultationSession is marked complete, THE Recommendation_Engine SHALL evaluate the Hair_Profile and produce at least 1 and at most 8 HairRecommendation records linked to that session within 5 seconds; WHEN the Recommendation_Engine is re-triggered for an existing completed session, it SHALL delete all previous HairRecommendation records for that session before producing new ones.
2. THE Recommendation_Engine SHALL map the hair_concern answer to Product records using a union (OR) match: a Product is eligible if any one of the User's selected hair_concern values matches any value in that Product's `targets` field.
3. THE Recommendation_Engine SHALL filter recommended Products to only include records where `product_range` is one of `ayurvedic`, `pharmacy`, or `treatment`.
4. WHILE a User's effective membership tier is `normal`, THE Recommendation_Engine SHALL exclude Products with a price greater than the `NORMAL_PRICE_MAX` setting from recommendations.
5. WHILE a User's effective membership tier is `medium`, THE Recommendation_Engine SHALL exclude Products with a price greater than the `MEDIUM_PRICE_MAX` setting from recommendations.
6. WHILE a User's effective membership tier is `vip`, THE Recommendation_Engine SHALL include all Products regardless of price; IF no UserProfile or membership tier record exists for the User, THEN THE Recommendation_Engine SHALL apply the `NORMAL_PRICE_MAX` price filter.
7. WHEN the Recommendation_Engine cannot find any matching Products for a completed ConsultationSession, THE Recommendation_Engine SHALL produce one HairRecommendation with a generic advisory note of at least 20 characters and no linked Product.
8. THE Lumina_System SHALL display HairRecommendation results on the consultation results page, showing product name, brand, price, a personalised explanation note of at least 20 characters, and a product image or a standard placeholder image if none is available.

---

### Requirement 6: Consultation Results Page

**User Story:** As a user, I want to view an attractive results page summarising my hair profile and recommended products after completing the quiz, so that I feel confident about the recommendations.

#### Acceptance Criteria

1. WHEN a User completes a ConsultationSession, THE Lumina_System SHALL render the consultation results page within 3 seconds of the final quiz submission.
2. THE Lumina_System SHALL display the User's Hair_Profile summary as individually labelled data points for each field: identified hair concerns, hair type, and scalp condition — in a visually styled card at the top of the results page.
3. THE Lumina_System SHALL display each HairRecommendation as an animated product card using AOS fade-up transitions, with a minimum 150 ms delay between successive cards.
4. WHEN a User clicks "Add to Cart" on a recommended product card, THE Lumina_System SHALL add the product to the user's active shopping session and confirm the action with a visible success message within 2 seconds; IF the add-to-cart operation fails, THEN THE Lumina_System SHALL display an error message on the results page without navigating away.
5. WHEN a User clicks "Retake Quiz" on the results page, THE Lumina_System SHALL create a new ConsultationSession and restart the quiz flow without deleting the previous session's data.
6. WHEN at least one completed ConsultationSession exists for a User, THE Lumina_System SHALL display a "My Hair Profile" link in the user profile section that navigates to the results page of the most recently completed session.
7. WHEN no completed ConsultationSession exists for a User, THE Lumina_System SHALL NOT display the "My Hair Profile" link in the user profile section.

---

### Requirement 7: SMS and WhatsApp Follow-Up Messaging

**User Story:** As a business owner, I want the system to send follow-up SMS and WhatsApp messages to users after consultation, so that users stay engaged and are reminded of their personalised plan.

#### Acceptance Criteria

1. WHEN a ConsultationSession is marked complete and the User has a verified phone number, THE Messaging_Service SHALL dispatch a WhatsApp message containing the User's top 3 product recommendations within 5 minutes of session completion.
2. WHEN a ConsultationSession is marked complete and the User has a verified phone number, THE Messaging_Service SHALL dispatch an SMS summary message containing the consultation results URL within 5 minutes of session completion.
3. WHEN one messaging channel (WhatsApp or SMS) dispatches successfully and the other fails for the same ConsultationSession completion event, THE Messaging_Service SHALL record the successful channel's OutboundMessage as `delivered` and the failed channel's OutboundMessage as `failed`, without retrying the failed channel.
4. WHEN a User has a completed ConsultationSession but has not placed any order within 72 hours of completion, THE Messaging_Service SHALL dispatch one follow-up WhatsApp reminder message with a link to the results page.
5. THE Messaging_Service SHALL create an OutboundMessage log record for every dispatched SMS and WhatsApp message, capturing recipient phone number, message type, provider response code, delivery status, and timestamp.
6. IF the external messaging provider returns an error response, THEN THE Messaging_Service SHALL record the provider error details in the OutboundMessage record, update the OutboundMessage status to `failed`, and SHALL NOT retry automatically; retries SHALL only occur when a staff member initiates a manual retry action via the admin interface.
7. WHEN both WhatsApp and SMS channels fail for the same ConsultationSession completion event, THE Messaging_Service SHALL record both OutboundMessage records as `failed` and the ConsultationSession SHALL remain identifiable in the admin OutboundMessage log view filtered by that User.
8. THE Lumina_System SHALL allow admin users to view OutboundMessage logs filtered by User, message type, delivery status, and date range in Django admin.
9. WHERE a User has opted out of marketing messages, THE Messaging_Service SHALL send only transactional messages (consultation summary) and SHALL suppress all follow-up reminder messages for that User.

---

### Requirement 8: User Phone Number Verification

**User Story:** As a user, I want to verify my phone number during or after the consultation, so that I can receive SMS and WhatsApp messages about my hair care plan.

#### Acceptance Criteria

1. THE Lumina_System SHALL present a phone number entry field during the final step of the consultation quiz or as a separate post-quiz prompt; the field SHALL accept E.164-formatted phone numbers only.
2. WHEN a User submits a phone number that does not match E.164 format, THE Lumina_System SHALL display a validation error and prevent OTP dispatch until a valid number is provided.
3. WHEN a User submits a valid E.164-formatted phone number, THE Lumina_System SHALL send a 6-digit OTP via SMS to the provided number within 60 seconds of the User's submission.
4. WHEN the User submits the correct OTP within 10 minutes of dispatch, THE Lumina_System SHALL mark the phone number as verified and associate it with the User's account.
5. IF the User submits an incorrect OTP, THEN THE Lumina_System SHALL display an error message and allow the User to re-enter the OTP up to 3 times before locking the current OTP and requiring the User to request a new one.
6. IF the OTP has expired (more than 10 minutes since dispatch), THEN THE Lumina_System SHALL reject the submission, display a message that the OTP has expired, and prompt the User to request a new OTP.
7. IF the User does not verify the phone number, THEN THE Lumina_System SHALL still complete the consultation and show results, skipping all SMS and WhatsApp follow-ups for that User.
8. THE Lumina_System SHALL store only the E.164-formatted phone number and its verification status; OTP values SHALL be invalidated and removed from storage after the earlier of successful verification or 10 minutes from dispatch.

---

### Requirement 9: Animated UI and Design

**User Story:** As a user, I want the consultation flow to have an engaging, modern animated interface, so that the experience feels premium and keeps me motivated to complete the quiz.

#### Acceptance Criteria

1. THE Quiz_UI SHALL use CSS keyframe animations or the AOS (Animate On Scroll) library already integrated in the project for all card entry and exit transitions.
2. THE Quiz_UI SHALL display a hair-themed gradient background on the quiz container where the dominant hue is in the amber-to-brown range (hue 20°–40°), distinct from the Lumina teal theme.
3. THE Quiz_UI SHALL render answer option cards with hover-lift transitions (translateY(-4px) on hover) consistent with the existing `.tier-card` CSS pattern.
4. WHEN a User advances to the next question, THE Quiz_UI SHALL update a linear animated progress indicator within 300 milliseconds, displaying the exact calculated percentage (questions_answered / total_questions * 100).
5. WHEN the consultation results are revealed, THE Quiz_UI SHALL play a sparkle particle micro-animation for 2 seconds using vanilla JavaScript with no additional npm dependencies.
6. THE Quiz_UI SHALL maintain WCAG 2.1 AA colour contrast ratios on all text and interactive elements throughout the quiz and results pages.
7. WHERE a User's browser or OS has `prefers-reduced-motion` enabled, THE Quiz_UI SHALL disable all CSS keyframe animations and AOS transitions and replace them with instant state changes.

---

### Requirement 10: Admin and Staff Management

**User Story:** As an admin, I want to view and manage consultation sessions, question banks, and messaging logs through Django admin, so that I can monitor the feature and make content updates without code changes.

#### Acceptance Criteria

1. THE Lumina_System SHALL register ConsultationSession, ConsultationAnswer, QuizQuestion, HairRecommendation, and OutboundMessage models in Django admin, each with at least 3 fields configured in list_display, at least 2 fields in list_filter, and at least 1 field in search_fields.
2. WHEN an admin triggers the Recommendation_Engine for a selected ConsultationSession from the Django admin change view, THE Lumina_System SHALL run the engine and display a success message listing the count of HairRecommendation records produced.
3. IF the manually triggered Recommendation_Engine run fails, THEN THE Lumina_System SHALL display an error message in the admin interface describing the failure and SHALL NOT alter the existing HairRecommendation records for that session.
4. WHEN an admin triggers a manual resend action for a failed OutboundMessage via the admin interface, THE Lumina_System SHALL attempt redelivery and update the OutboundMessage delivery status and timestamp accordingly.
5. IF the manual resend attempt fails, THEN THE Lumina_System SHALL display an error message in the admin interface and retain the OutboundMessage status as `failed`.
6. WHEN an admin deactivates a QuizQuestion, THE Lumina_System SHALL always display a confirmation prompt showing the count of active ConsultationSessions that reference that question before saving the change, even when the count is zero.
7. THE Lumina_System SHALL provide an admin dashboard widget on the employee portal showing total consultations completed (today counted from midnight in the server's configured timezone, this week counted from Monday 00:00 in the server's configured timezone, and all-time), SMS sent count, and WhatsApp sent count.

---

### Requirement 11: Data Privacy and Retention

**User Story:** As a user, I want my hair health and personal data handled securely, so that I can trust the platform with sensitive health information.

#### Acceptance Criteria

1. THE Lumina_System SHALL store ConsultationSession and ConsultationAnswer records only when the creating User is authenticated at the time of record creation.
2. IF an unauthenticated session contains in-progress consultation data, THEN THE Lumina_System SHALL clear that data when the browser session ends without persisting it to the database.
3. WHEN a User deletes their account, THE Lumina_System SHALL delete all ConsultationSession, ConsultationAnswer, HairRecommendation, and OutboundMessage records belonging to that User; IF any of these deletions fail due to a database error, THEN THE Lumina_System SHALL log the IDs of all records that were not deleted and SHALL NOT block the account deletion from completing.
4. THE Lumina_System SHALL NOT include individual question-answer pairs or user identity information in any data transmitted to the SMS or WhatsApp provider; only the pre-formatted message text SHALL be sent.
5. THE Lumina_System SHALL store phone numbers in an encrypted form at rest such that the plain-text value is not stored in the primary database column.
6. WHEN a User reaches the consultation quiz start page, THE Lumina_System SHALL display a data consent notice explaining what data is collected and how it is used before presenting the first quiz question.
7. WHEN a User acknowledges the consent notice by checking the acknowledgement checkbox, THE Lumina_System SHALL record the acknowledgement and allow the User to proceed to the first question; IF the User attempts to proceed without checking the checkbox, THEN THE Lumina_System SHALL prevent navigation to the first question and display a message requiring acknowledgement.
