# Smart Intent Router – Interface Spec

Single HTTP endpoint used by the voice agent (e.g. ElevenLabs) for sync, patient, availability, booking, cancel, reschedule, details, and service-info flows. The router infers or accepts an intent, normalizes the payload, and dispatches to the appropriate handler.

---

## Endpoint

| Method | Path        | Auth                    |
|--------|-------------|-------------------------|
| POST   | `/voice-agent` | API key (dependency) |

Request body: JSON object (`Dict[str, Any]`). No path or query parameters required.

**Backward compatibility:** `POST /api/v1/voice-agent` forwards to the same handler.

---

## Request Schema

The body is a single JSON object. All fields are optional unless stated. The router accepts both canonical names and voice-agent aliases; canonical names take precedence.

### Required for most intents

| Field            | Type   | Description |
|------------------|--------|-------------|
| `session_id`     | string | Unique identifier for the conversation session (required for context persistence). |
| `dialed_number`  | string | Number dialed (clinic). Aliases: `called_number`, `system__called_number`. |
| `caller_phone`   | string | Caller phone. Aliases: `caller_id`, `system__caller_id`. |
| `conversation_id`| string | ElevenLabs conversation identifier. |

**ElevenLabs tool config:** Configure `called_number`/`dialed_number`, `caller_id`/`caller_phone`, and `conversation_id` as **dynamic_variable** (e.g. `system__called_number`, `system__caller_id`, `system__conversation_id`) so they are auto-populated from the system.

### Intent and routing

| Field    | Type   | Description |
|----------|--------|-------------|
| `intent` | string | One of the supported intents (see below). Aliases: `action`. |
| `session_id` | string | Optional. If omitted, one is generated; silent init (clinic lookup, optional sync) runs for non-sync intents. |

### Location / business

| Field           | Type   | Description |
|-----------------|--------|-------------|
| `business_name` | string | Location/business name. Aliases: `location`, `business`, `clinic`, `office` (and capitalized variants). |
| `business_id`   | string | Pre-resolved business ID. |

### Practitioner and service

| Field                 | Type   | Description |
|-----------------------|--------|-------------|
| `practitioner`        | string | Practitioner name. |
| `practitioner_id`     | string | Pre-resolved practitioner ID. |
| `appointment_type`     | string | Service/appointment type name. Aliases: `service`, `treatment`, `treatment_name`. |
| `appointment_type_id`  | string | Pre-resolved appointment type ID. Aliases: `service_id`, `treatment_id`. |

### Date and time

| Field             | Type   | Description |
|-------------------|--------|-------------|
| `date`            | string | Date (YYYY-MM-DD). Aliases: `appointment_date`, `start_date` (for availability). |
| `time`            | string | Time. Alias: `appointment_time`. |
| `start_date`      | string | Used by `find_next_available` (YYYY-MM-DD). If absent, `date`/`appointment_date` are mapped to it. |
| `preferred_time`  | string | e.g. morning/afternoon/evening, or "after 2pm". Alias: `preferredTime`. |
| `max_days`        | int    | Used by `find_next_available` (default 2). |
| `detail`          | string | For `find_next_available` and `availability`: `"summary"` = day names only, no slots; `"slots"` = full `individual_slots` (default). Omit for backward compatibility (defaults to `"slots"`). |

### Booking and patient

| Field           | Type   | Description |
|-----------------|--------|-------------|
| `booking_for`   | string | `"self"` or `"other"`. |
| `patient_name`  | string | Patient name. |
| `patient_phone` | string | Patient phone. |
| `patient_email` | string | Patient email. |
| `appointment_id`| string | For cancel/reschedule/details. |
| `appointment_details` | string | For lookup/details. |
| `new_date`      | string | For reschedule. |
| `new_time`      | string | For reschedule. |
| `cancellation_reason` / `reason` | string | For cancel. |

### Other

| Field            | Type   | Description |
|------------------|--------|-------------|
| `raw_user_input` | string | Raw user utterance; used for intent inference and messaging. |
| `clinic_id`      | string | Set by router during silent init; can be sent. |
| `clinic_name`    | string | Set by router; can be sent. |
| `force_full_sync`| bool   | For sync intent (default false). |

**Filtering:** Values equal to (or containing) `"unknown"` in `practitioner`, `business_name`, `location`, `appointment_type`, `patient_name` are cleared before processing.

**Service normalization:** `treatment`/`treatment_name` and `treatment_id` are mapped to `appointment_type`/`appointment_type_id`; `service`/`service_id` and `appointment_type`/`appointment_type_id` are cross-filled when one side is missing.

---

## Response Schema

All responses are JSON objects.

### Common fields (all intents)

| Field         | Type    | Description |
|---------------|---------|-------------|
| `success`     | boolean | Whether the operation succeeded. |
| `message`     | string  | Human-readable message for the agent to speak. |
| `session_id`  | string  | Session ID (generated or echoed). |
| `tool_status` | string  | Optional. e.g. `"completed"`, `"failed"`. |
| `completion_status` | string | Optional. e.g. `"success"`, `"error"`. |

### Error response (intent not found, unsupported intent, or other router-level failure)

| Field               | Type     | Description |
|---------------------|----------|-------------|
| `success`           | false    | |
| `error`             | string   | One of: `"intent_not_found"` (could not determine intent), `"unsupported_intent"` (intent not in dispatch list), `"validation_error"` (Pydantic validation failed in a handler), `"clinic_not_found"`, `"initialization_failed"`, `"internal_error"` (unexpected exception in the router), `"trial_ended_subscription_required"` (trial ended and no active subscription; see `tools/access_control.py`). |
| `message`           | string   | Error message. |
| `session_id`        | string   | |
| `supported_intents` | string[] | Present when `error` is `"intent_not_found"` or `"unsupported_intent"`. |
| `details`           | array    | Present when `error == "validation_error"` (Pydantic validation error details). |

### Routing and context (on success)

The router may add routing flags and context variables to the response (for workflow edges and dynamic variables):

- **Primary intent flags (preserved; DO NOT consolidate):** `availability_checked`, `booking_completed`, `cancellation_completed`, `patient_lookup_done`. These remain the authoritative success flags for the primary business intents (availability/search, book, cancel, patient lookup).
- **Routing-only consolidated intent:** `uni_router_intent` (string). This is used only as a transition trigger between workflow nodes for non-primary routing events.
- **Legacy routing-only flags (deprecated for edges; still returned for clearing):** `service_resolved`, `extended_swapped`, `booking_route_resolved`, `reschedule_routed`, `service_info_retrieved`, `constraint_change_routed`, `recommendation_ready`, `recommendation_exhausted`.
- **Context variables** (validated from payload): e.g. `booking_for`, `practitioner_preference`, `timeframe_raw`, `preferred_gender`, `location`, `massage_duration`, `patient_status`, `group_or_private`, `implied_service`.
- For availability/find_next_available (and `confirm_time` when used by the workflow), when a patient object is present: `caller_first_name`, `caller_last_name`, `caller_email`; for `confirm_time`, `can_go_self_booking` is set from booking route.

#### `uni_router_intent` values (routing-only)

When present, `uni_router_intent` is one of:

- `"service_resolved"`: service confirmation completed (service resolution → availability handler transition).
- `"constraint_change"`: caller wants to change time/practitioner/location (constraint-change router → availability handler transition).
- `"service_change"`: caller wants to change service (constraint-change router → service resolution transition).
- `"reschedule"`: reschedule path selected.
- `"service_info"`: service information request routed/ready.
- `"booking_self"`: route to self booking name-collection path.
- `"booking_other"`: route to other-person booking name-collection path.
- `"extended_swapped"`: extended variant swap completed.
- `"recommendation_ready"` / `"recommendation_exhausted"`: recommendation path result is ready / exhausted.

#### Clearing rules (critical)

- For **primary intent successes** (availability/book/cancel/find_patient): `uni_router_intent` is explicitly returned as `""` to prevent stale routing-only triggers leaking into later edges.
- For **routing-only intents** (the values above): the router **explicitly returns `""`** for the 4 preserved primary flags (`availability_checked`, `booking_completed`, `cancellation_completed`, `patient_lookup_done`) so they do not accidentally remain set from earlier turns.

### Intent-specific response fields

- **sync:** `sync_status` (e.g. `"started_in_background"`).
- **initialize_call:** `clinic_name`, `clinic_id`, `locations` (array of `{ business_name, business_id, address }`).
- **create_patient / find_patient:** Handler-defined (e.g. patient id, created flag).
- **payload_status:** `payload_completeness` (e.g. `complete`, `missing_fields`), `detected_intent`.
- **book:** Handler-defined (e.g. appointment id, confirmation). The returned `message` (spoken confirmation) uses the **category name** (e.g. "[category]") for the service, not the appointment type name (e.g. "[appointment type]"). Reschedule confirmation message uses category name when available, else appointment type name.
  - **Dynamic variable persistence (book success)**:
    - `appointment_id` is returned by the booking handler and is mapped (via ElevenLabs tool assignments) to dynamic variable `recent_booking_id`.
    - `recent_booking_phone` is returned on every successful booking completion and is mapped to dynamic variable `recent_booking_phone`.
    - `recent_booking_phone` is **never** returned as `""` on booking success; it is only cleared by Wrap Router on Node 9 exit.
- **find_next_available:** `alternative_slots`, `earliest_slot`, handler message.
- **availability / check_availability / slots:** After reshaping for the agent: `date`, `patient` (name, email, first_name, last_name), `locations` (array of `{ id, name, practitioners: [{ id, first_name, individual_slots }] }`), `resolved_context`. Backend-only fields such as `conversational_groups` are removed before return.
- **get_available_practitioners:** List of practitioners (handler-defined).
- **cancel / reschedule / details:** Handler-defined (e.g. cancellation confirmation, appointment details).
- **details_past:** `had_appointments` (bool), `appointment_type_names` (list of strings; distinct appointment type names the caller has had, no IDs), `message` (TTS).
- **get_service_info / appointment_type_info:** Service info (e.g. pricing, duration).
- **recommend_availability:** Recommendation payload (handler-defined). May set `recommendation_ready` or `recommendation_exhausted` to `"true"`/`"false"`. `tool_status`/`completion_status` can be set to completed/success when either `recommendation_ready` or `recommendation_exhausted` is true even if `success` is false.

---

## Supported Intents

| Intent | Description | Typical handler |
|--------|-------------|-----------------|
| `initialize_call` | Starts session, performs background sync, and retrieves clinic locations. | Inline (DB + sync) |
| `payload_status` | Report what is missing for the current flow (book/availability/cancel/reschedule/details). | `get_payload_completeness` |
| `availability` / `slots` | Checks availability for a specific practitioner/date/service. Handles narrowing follow-ups. | `smart_availability` |
| `find_next_available` | Next available slots (from a start date, optional practitioner/service/location). | `find_next_available` |
| `book` / `appointment` | Create appointment. Clears `booking_for` on success. | `handle_appointment` |
| `cancel` | Cancel an appointment. Handles multi-turn policy overrides. | `cancel_appointment` |
| `reschedule` | Reschedule an appointment. | `reschedule_appointment` |
| `details` | Get future appointment details (e.g. “when is my appointment”). | `get_appointment_details` |
| `details_past` | Past appointment history: which appointment types the caller has had. | `get_appointment_details_past` |
| `get_service_info` | Service/appointment type info (e.g. pricing, duration). | Service info handler |
| `recommend_availability` | Provides a long-term "recommendation" for availability. | Recommend-availability handler |
| `get_available_practitioners` | Returns a list of practitioners working at the clinic. | Availability handler |
| `find_patient` | Look up patient (e.g. by phone). | `find_patient` |
| `create_patient` | Create patient (e.g. in Cliniko). | `create_patient` |
| `sync` | Start cache sync in background; return immediately. | `sync_cache` |

Intent is taken from `intent` or `action` first. If missing, it is inferred from `raw_user_input` (e.g. “book”/“availability”/“next available” phrases) or from payload keys (e.g. presence of `sync`, `book`, `cancel`). If `booking_for == "self"` and `caller_id` is set with no other intent, intent becomes `book`. Intent is lowercased before dispatch.

---

## Logic & Session Management

1. **Field mapping**  
   Voice-agent fields are mapped to canonical names: `called_number` → `dialed_number`; `caller_id` → `caller_phone`. Weekdays are resolved to the next occurring date.

2. **Session Persistence**  
   Uses `SessionManager` (PostgreSQL) to store `available_slots`, `earliest_slot`, `last_response`, and `last_requested_time/date`.

3. **Smart Detection**  
   - **Narrowing Follow-ups**: Detects when a user asks narrowing questions (e.g., "How about the morning?") after a broad search and routes to `find_next_available`.
   - **Anything else?**: Detects "Anything else?" queries and clears the current objective while preserving the session.

4. **Service normalization**  
   Maps `treatment` to `appointment_type`. Cross-fills service IDs.

5. **Response shaping**  
   Returns `tool_status` and `completion_status`. Attaches session context. Includes `goal_tracking`. Filters out internal fields (prefixed with `_`). Grouped by location: `locations[]` with `practitioners[]` and `individual_slots`.

---

## Request/Response Model References

Under the hood the router maps the JSON body into these Pydantic models (from `models.py`) before calling handlers:

- **Sync:** `SyncCacheRequest` (session_id, dialed_number, caller_phone, force_full_sync)
- **Patient:** `PatientCreationRequest` (session_id, dialed_number, caller_phone, patient_name, patient_phone, patient_email, create_in_cliniko)
- **Availability:** `AvailabilityRequest` (session_id, dialed_number, caller_phone, practitioner, date, appointment_type, appointment_type_id, business_name, business_id, preferred_time, booking_for, patient_status, raw_user_input, etc.)
- **Book:** `BookingRequest` (session_id, dialed_number, caller_phone, patient_name, appointment_type, practitioner, practitioner_id, appointment_date, appointment_time, business_name, business_id, appointment_type_id, booking_for, etc.)
- **Find next available:** `FindNextAvailableRequest` (session_id, dialed_number, caller_phone, practitioner, practitioner_id, service, appointment_type_id, business_id, business_name, start_date, max_days, preferred_time, booking_for, etc.)
- **Cancel:** `CancelAppointmentRequest` (session_id, dialed_number, caller_phone, appointment_id, appointment_details, cancellation_reason, etc.)
- **Reschedule:** Uses booking/reschedule handler with `BookingRequest`-like payload (new_date, new_time, etc.)
- **Details:** `GetAppointmentDetailsRequest` (session_id, dialed_number, caller_phone, appointment_id, appointment_details, raw_user_input)
- **Details past:** `GetAppointmentDetailsPastRequest` (session_id, dialed_number, caller_phone)

All of these allow optional or defaulted fields; the router fills from the merged payload and may add defaults (e.g. `start_date` for find_next_available when absent).
