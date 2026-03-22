# Universal Router Webhook – Interface Specification

**Endpoints:**  
- `POST /api/v1/webhook/universal_router` – main routing tool (intent + payload).  
- `POST /api/v1/webhook/wrap_router` – Wrap Up (Node 9) routing; see section 6.

**Auth:** API key required via `X-API-Key` or `X-Api-Key` header (both endpoints).  
**Purpose:** Accepts tool calls from the ElevenLabs Routing Edge LLM with an intent and optional payload; returns success plus intent and payload promoted to top level so ElevenLabs can map them to dynamic variables (`{{variable_name}}`). `session_id` is never returned (must only be written by smart_voice_agent).

---

## 1. Universal Router – Request schema

| Field        | Type                    | Required | Description |
|-------------|-------------------------|----------|-------------|
| `intent`    | string                  | Yes      | Primary routing flag (see Supported intents). |
| `payload`   | object \| string \| null | No       | Optional catch-all for LLM-collected variables (e.g. `appointment_type_id`, `practitioner_id`). If string, parsed as JSON; invalid or non-object becomes `{}`. |
| `called_number` | string \| null      | No       | Dialed number for clinic context (extended variants, etc.). Accepts `called_number`, `dialed_number`, or `system__called_number` (with or without +61). |
| `dialed_number` | string \| null      | No       | Same as `called_number`; either key is accepted. |
| `system__called_number` | string \| null | No       | ElevenLabs system variable for dialed number (with or without +61). |
| `caller_id` | string \| null          | No       | Caller phone (with or without +61). |
| `caller_phone` | string \| null        | No       | Same as `caller_id`. |
| `system__caller_id` | string \| null     | No       | ElevenLabs system variable for caller number. |
| `system__caller_phone` | string \| null  | No       | ElevenLabs system variable for caller phone. |
| `session_id`    | string \| null      | No       | Session ID (e.g. `{{session_id}}`). When provided with `booking_for`, stores `booking_for` in session until booking completes or `booking_for` changes. Never echoed in response. |

Called number is resolved from body or payload: `called_number`, `dialed_number`, `system__called_number` (first non-empty wins).

**ElevenLabs tool config:** Configure `called_number`, `caller_id`, and `conversation_id` as **dynamic_variable** (e.g. `system__called_number`, `system__caller_id`, `system__conversation_id`) so they are auto-populated from the system. The LLM then need not pass them, avoiding omission or hallucination (see README §7). Do **not** add an assignment that maps response `session_id` to a dynamic variable; the universal router never returns `session_id`.

**Example (minimal):**
```json
{
  "intent": "confirm_service",
  "payload": { "appointment_type_id": "123" }
}
```

**Example (full):**
```json
{
  "intent": "capture_context",
  "payload": {
    "booking_for": "self",
    "practitioner_preference": "[name]",
    "timeframe_raw": "[timeframe]"
  },
  "called_number": "+61...",
  "session_id": "abc-123"
}
```

---

## 2. Universal Router – Response schema

All successful responses include at least:

| Field     | Type   | Description |
|----------|--------|-------------|
| `status` | string | `"success"` |
| `intent` | string | Echo of request `intent`. |

Additional top-level fields depend on intent and payload:

- **Intent-specific injections** (see Logic): e.g. `booking_for`, `appointment_date`, `appointment_time`, `practitioner_id`, `appointment_type`, `appointment_type_id`, `variant_type`, `patient_status`, `working_length_type`, `business_id`, `business_name`, or cleared variants of these (empty string `""` for clear intents).
- **Echoed payload:** Any key from `payload` that is not already set on the response is copied to the response (so ElevenLabs can map to dynamic variables). **`session_id` is never echoed** (must only be written by smart_voice_agent).
- **Routing outputs:** This webhook emits:
  - `uni_router_intent` (string routing-only transition intent; see below)
  - the 4 preserved primary intent flags: `availability_checked`, `booking_completed`, `cancellation_completed`, `patient_lookup_done`
  - legacy routing-only flags (deprecated for edges; still returned for explicit clearing): `service_resolved`, `extended_swapped`, `booking_route_resolved`, `reschedule_routed`, `service_info_retrieved`, `constraint_change_routed`, `service_change_routed`

**Critical clearing rule:** The workflow depends on variables being explicitly returned as `""` to clear state. When `uni_router_intent` is used for a routing-only transition, this webhook MUST also explicitly return `""` for the 4 preserved primary flags.

### 2.1 `uni_router_intent` (routing-only transition values)

`uni_router_intent` is one of:

- `"service_resolved"`
- `"constraint_change"`
- `"service_change"`
- `"reschedule"`
- `"reschedule_pending"`
- `"reschedule_same"`
- `"reschedule_different"`
- `"service_info"`
- `"booking_self"`
- `"booking_other"`
- `"retry_booking_self"`
- `"retry_booking_other"`
- `"retry_cancel"`
- `"retry_availability"`
- `"reschedule_cancelled"`
- `"extended_swapped"`
- `"recommendation_ready"`
- `"recommendation_exhausted"`
- `"wrap_up"`
- `"return_to_origin"`
- `"info_from_[source]"` (e.g., `info_from_cancellation`)

For primary business intents (availability/book/cancel/find_patient) this field is returned as `""` to reset any previous routing-only trigger.

**Example (confirm_service with extended variant):**
```json
{
  "status": "success",
  "message": "Routed successfully",
  "intent": "confirm_service",
  "uni_router_intent": "service_resolved",
  "appointment_type_id": "123",
  "extended_variant_available": true,
  "extended_appointment_type_id": "456",
  "extended_appointment_type": "[extended name]",
  "availability_checked": "",
  "booking_completed": "",
  "cancellation_completed": "",
  "patient_lookup_done": "",
  "service_resolved": "",
  "extended_swapped": "",
  "booking_route_resolved": "",
  "reschedule_routed": "",
  "service_info_retrieved": "",
  "constraint_change_routed": "",
  "service_change_routed": ""
}
```

**Example (capture_context):**
```json
{
  "status": "success",
  "intent": "capture_context",
  "uni_router_intent": "",
  "booking_for": "self",
  "practitioner_preference": "[name]"
}
```

---

## 3. Universal Router – Supported intents

| Intent                | Routing flag set                    | Notes |
|-----------------------|-------------------------------------|--------|
| `initialize_call`     | `uni_router_intent` = `""`          | Early return includes `uni_router_intent: ""` plus `booking_for: "self"`. |
| `confirm_service`     | `uni_router_intent` = `"service_resolved"` | May add `extended_variant_available`, `extended_appointment_type_id`, `extended_appointment_type` when clinic + `appointment_type_id` + extended pairing exist. Clears the 4 preserved primary flags to `""`. |
| `availability`        | `availability_checked` = `"true"`   | Sets `uni_router_intent` = `""`. |
| `find_next_available` | `availability_checked` = `"true"`   | Sets `uni_router_intent` = `""`. |
| `confirm_time`        | `availability_checked` = `"true"`   | Also sets `uni_router_intent` to `"booking_self"` or `"booking_other"` when availability is checked and `booking_for` is self/other. |
| `swap_extended`       | `uni_router_intent` = `"extended_swapped"` | Swaps to extended variant when mapping exists; always sets `working_length_type` = `"extended"`. Clears the 4 preserved primary flags to `""`. |
| `route_self`          | `uni_router_intent` = `"booking_self"` | Injects `booking_for` = `"self"`. Clears the 4 preserved primary flags to `""`. |
| `route_other`         | `uni_router_intent` = `"booking_other"` | Injects `booking_for` = `"other"`. Clears the 4 preserved primary flags to `""`. |
| `find_patient`        | `patient_lookup_done` = `"true"`    | Sets `uni_router_intent` = `""`. |
| `book`                | `booking_completed` = `"true"`      | Sets `uni_router_intent` = `""`. |
| `cancel`              | `cancellation_completed` = `"true"` | Sets `uni_router_intent` = `""`. |
| `reschedule`          | `uni_router_intent` = `"reschedule"` | Clears the 4 preserved primary flags to `""`. |
| `get_service_info`    | `uni_router_intent` = `"service_info"` | Clears the 4 preserved primary flags to `""`. |
| `change_time`         | `uni_router_intent` = `"constraint_change"` | Clears `appointment_date`, `appointment_time` to `""`. Clears the 4 preserved primary flags to `""`. |
| `change_practitioner` | `uni_router_intent` = `"constraint_change"` | Clears `practitioner_id` to `""`. Clears the 4 preserved primary flags to `""`. |
| `change_service`      | `uni_router_intent` = `"service_change"` | Clears service + related fields to `""`. Clears the 4 preserved primary flags to `""`. |
| `change_location`     | `uni_router_intent` = `"constraint_change"` | Clears `business_id`, `business_name` to `""`. Clears the 4 preserved primary flags to `""`. |
| `multiple_changes`    | `uni_router_intent` = `"constraint_change"` | Clears fields based on payload: `clear_time`, `clear_practitioner`, `clear_service`, `clear_location`. Clears the 4 preserved primary flags to `""`. |
| `constraint_change` | `uni_router_intent` = `"constraint_change"` | Same routing semantics as `change_*` when the constraint type is already known (e.g. pivot escape). Clears the 4 preserved primary flags to `""`. |
| `wrap_up`             | `uni_router_intent` = `"wrap_up"` | Routing-only full-session signal. Clears the 4 preserved primary flags to `""`. |
| `return_to_origin`   | `uni_router_intent` = `"return_to_origin"` | Removes `return_node` to break circular paths. |
| `retry_availability` | `uni_router_intent` = `"retry_availability"` | Node 11 routing signal. Clears 4 primary flags. No context changes. |
| `retry_cancel`       | `uni_router_intent` = `"retry_cancel"` | Node 11 routing signal. Clears 4 primary flags. No context changes. |
| `retry_booking_self` | `uni_router_intent` = `"retry_booking_self"` | Node 11 routing signal. Clears 4 primary flags. No context changes. |
| `retry_booking_other`| `uni_router_intent` = `"retry_booking_other"` | Node 11 routing signal. Clears 4 primary flags. No context changes. |
| `reschedule_cancelled` | `uni_router_intent` = `"reschedule_cancelled"` | Routing-only; explicitly clears `reschedule_mode` to `""`. Clears 4 primary flags. |
| `capture_context`     | `uni_router_intent` depends on payload | Context-only; validates and echoes context fields. If `cancellation_rebooking_mode` is provided: `"pending" → "reschedule_pending"`, `"same" → "reschedule_same"`, `"different" → "reschedule_different"`, `"retry_booking" → "retry_booking_self/other"`. Also handles `info_pivot_source`. |

Intents not listed above receive all 11 routing flag keys with value `""`.

---

## 4. Context fields (payload validation)

For `capture_context` and for echoing into the response, these payload keys are validated. Invalid or disallowed values are omitted (silent drop). Only keys present in the payload are returned.

| Key                     | Allowed values / behaviour |
|-------------------------|-----------------------------|
| `booking_for`           | `"self"`, `"other"` |
| `practitioner_preference` | Any string (or `"none"`) |
| `timeframe_raw`         | Any string |
| `preferred_gender`      | `"male"`, `"female"` |
| `implied_service`       | Any string |
| `location`              | Any string |
| `massage_duration`      | `"30"`, `"45"`, `"60"`, `"90"` |
| `patient_status`        | `"new"`, `"existing"` |
| `group_or_private`      | `"group"`, `"private"` |
| `reschedule_mode`       | `"true"` (set/cleared per 5.1) |
| `constraint_change_source` | Any node identifier string (set/cleared per 5.1) |
| `return_node`           | Any node identifier string (echoed when present in payload; see logic for interaction with `change_*` intents) |

Non-string or empty-after-trim values are omitted.

**Note:** `caller_complaint` is captured via this tool or the async context capture tool (`tools/async_capture_context_webhook.py`). The wrap router clears `caller_complaint` on most wrap intents.

### 4.1 Information Pivots
The `capture_context` intent handles synchronous informational pivots via `info_pivot_source` in the payload.
- `info_pivot_source: "cancellation"` sets `uni_router_intent` to `info_from_cancellation`.

---

## 5. Universal Router – Logic summary

1. **Parse payload:** `payload` may be object or JSON string; non-object or parse failure becomes `{}`.
2. **capture_context:** Validate and extract context fields; return `status`, `intent`, `uni_router_intent: ""`, and valid context only. If `session_id` and valid `booking_for` in `("self","other")`, persist `booking_for` to session (non-blocking).
3. **initialize_call:** Early return includes `uni_router_intent: ""` plus `booking_for: "self"`.
4. **Build base response:** Set `status` = `"success"`, `message` = `"Routed successfully"`, `intent` = request intent. Apply intent-specific injections:
   - `route_self` / `route_other`: set `booking_for`.
   - `change_time`: set `appointment_date`, `appointment_time` to `""`.
   - `change_practitioner`: set `practitioner_id` to `""`.
   - `change_service`: clear appointment-type and related fields to `""`.
   - `change_location`: clear `business_id`, `business_name` to `""`.
   - `multiple_changes`: clear fields according to `clear_time`, `clear_practitioner`, `clear_service`, `clear_location` in payload.
5. **Aggressive Constraint Wiping**: Wiping ephemeral variables once logical gates are passed:
   - `confirm_service`: Wipes `massage_duration`, `implied_service`, `group_or_private`.
   - `confirm_time`: Wipes `extended_variant_available`, `extended_appointment_type`, `extended_appointment_type_id`, `working_length_type`.
6. **Echo payload:** For each payload key not already in the response, add it to the response. **Never echo `session_id`.**
7. **Extended variant (confirm_service / swap_extended):** Resolve called number from body or payload. Lookup extended variant in `extended_variant_pairings`.
8. **Routing outputs:**
   - For primary business intents, set the preserved primary flag to `"true"` and clear `uni_router_intent`.
   - For routing-only intents, set `uni_router_intent` and explicitly return `""` for primary flags.
9. **Reschedule Wipes (capture_context)**:
   - `reschedule_same`: Wipes `appointment_date`, `appointment_time`, `timeframe_raw`, `practitioner_preference`.
   - `reschedule_different`: Wipes all of the above plus `appointment_type`, `appointment_type_id`, `variant_type`, `patient_status`, `working_length_type`.
10. **confirm_time:** If availability was checked, set `uni_router_intent` to `"booking_self"` or `"booking_other"`.
11. **reschedule_cancelled:** Explicitly resets `reschedule_mode` to `""`.
12. **Session persistence:** Persist `booking_for` to session.

Result: a single JSON object with `status`, `intent`, optional `message`, intent-specific fields, echoed payload (excluding `session_id`), routing flags, and optional context, suitable for mapping to ElevenLabs dynamic variables.

---

## 5.1 New dynamic variables (set/clear behaviour)

| Variable | Set | Values | Clear |
|----------|-----|--------|--------|
| `return_node` | On any `change_*` intent: copy value of `constraint_change_source` into `return_node` | Any node identifier string | On any non-`change_*` intent |
| `reschedule_mode` | By `capture_context` when payload includes `reschedule_mode` | `"true"` | On `wrap_cancel` intent |
| `constraint_change_source` | By `capture_context` when payload includes `constraint_change_source` | Any node identifier string | On any `change_*` intent after copying to `return_node` |

- **capture_context:** For these variables, only keys present in the payload are echoed; validate `reschedule_mode` to `"true"`; `constraint_change_source` accepts any non-empty string. If `reschedule_mode == "true"`, `cancellation_rebooking_mode` (payload-only) may be used to set `uni_router_intent` to `"reschedule_pending"`, `"reschedule_same"`, or `"reschedule_different"` (see section 3); it is not persisted as a dynamic variable.
- **Wrap Router:** For `wrap_cancel`, the response includes `reschedule_mode`, `return_node`, and `constraint_change_source` set to `""` so ElevenLabs clears them.

---

## 6. Wrap Router (Node 9 Wrap Up)

**Endpoint:** `POST /api/v1/webhook/wrap_router`  
**Auth:** Same as universal router (`X-API-Key` or `X-Api-Key`).

### 6.1 Request schema

| Field        | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `intent`    | string | Yes      | One of: `wrap_new_unknown`, `wrap_new_known`, `wrap_cancel`, `wrap_reschedule`, `wrap_info`, `wrap_modify`, `wrap_restart`. |
| `called_number` | string \| null | No | Dialed number (pass-through only). Accepts `called_number`, `dialed_number`, or `system__called_number` (with or without +61). |
| `dialed_number` | string \| null | No | Same as `called_number`. |
| `system__called_number` | string \| null | No | ElevenLabs system variable for dialed number. |

Unsupported intents return `400` with detail listing allowed intents.

### 6.2 Response schema

Success response includes:

- `status`: `"success"`
- `intent`: echo of request intent
- `wrap_routing_flag`: one of `new_unknown`, `new_known`, `cancel`, `info`, `modify`, `restart`
- `booking_for`: `"self"` except for `wrap_cancel`, `wrap_reschedule`, and `wrap_info` (then `""`)
- `recent_booking_phone`: `""` (cleared on Node 9 exit only)
- All booking/context fields set to `""` (except for `wrap_new_known` - see below).
- `caller_complaint` is cleared to `""`.
- `uni_router_intent`, primary flags, and legacy flags are all set to `""`.
- `return_node` and `constraint_change_source` are set to `""`.

For `wrap_new_known` only: `appointment_type_id` and `appointment_type` are omitted (to preserve existing service context). For all other wrap intents they are set to `""`.

Cleared on wrap (so ElevenLabs can reset them): `return_node`, `constraint_change_source` are always included in the wrap response as `""`.

`reschedule_mode` behaviour:
- `wrap_cancel`: `reschedule_mode` is cleared to `""`
- `wrap_reschedule`: `reschedule_mode` is preserved as `"true"`

### 6.3 Supported wrap intents

| Intent             | `wrap_routing_flag` | `booking_for` |
|--------------------|---------------------|---------------|
| `wrap_new_unknown` | `new_unknown`       | `self`        |
| `wrap_new_known`   | `new_known`         | `self`        |
| `wrap_cancel`      | `cancel`            | `""`          |
| `wrap_reschedule`  | `cancel`            | `""`          |
| `wrap_info`        | `info`              | `""`          |
| `wrap_modify`      | `modify`            | `self`        |
| `wrap_restart`     | `restart`           | `self`        |

### 6.4 Ghost Context Clearing Logic
- **`wrap_new_unknown`, `wrap_restart`, `wrap_modify`**: Full constraint wipe (clears `timeframe_raw`, `practitioner_preference`, `location`, `massage_duration`, etc.).
- **`wrap_new_known`**: Partial wipe. Preserves `practitioner_preference` and `location` for same-service rebooking.
- **`wrap_cancel`, `wrap_reschedule`, `wrap_info`**: No constraint clearing (context needed for these nodes). Wins `reschedule_mode` preservation on `wrap_reschedule`.
