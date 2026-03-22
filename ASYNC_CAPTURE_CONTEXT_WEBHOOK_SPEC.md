# Async Context Capture Webhook – Interface Specification

**Endpoint:** `POST /async-capture-context`  
**Auth:** API key required via `X-API-Key` or `X-Api-Key` header.  
**Purpose:** A fire-and-forget (ASYNC) tool for ElevenLabs. Persists volunteered booking preferences into the session's `resolved_context` and ElevenLabs dynamic variables when no other tool call is being made in the same turn.

---

## 1. Request Schema

| Field | Type | Description |
|---|---|---|
| `payload` | object | Dictionary of volunteered context variables. |
| `session_id` | string | Session ID for persisting context. |
| `called_number` | string | Dialed number (automated from system). |
| `caller_id` | string | Caller phone (automated from system). |
| `conversation_id` | string | ElevenLabs conversation ID. |

---

## 2. Capturable Fields

The tool validates the `payload` against this strict allowlist. Invalid values or unlisted keys are ignored.

| Key | Validation / Allowed Values |
|---|---|
| `booking_for` | `"self"`, `"other"` |
| `practitioner_preference`| Any string |
| `timeframe_raw` | Any string |
| `preferred_gender` | `"male"`, `"female"` |
| `implied_service` | Any string |
| `location` | Any string |
| `massage_duration` | `"30"`, `"45"`, `"60"`, `"90"` |
| `patient_status` | `"new"`, `"existing"` |
| `group_or_private` | `"group"`, `"private"` |
| `reschedule_mode` | `"true"` |
| `caller_complaint` | Any string |

---

## 3. Response Schema

ElevenLabs maps **top-level** response keys to dynamic variables. This tool promotes all successfully captured fields to the top level.

| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` |
| `captured` | object | Dictionary of all successfully validated fields (for logging). |
| `[field_name]` | string | Every captured field (e.g., `location`, `timeframe_raw`) is echoed at the top level. |

**Example Response:**
```json
{
  "success": true,
  "captured": {
    "location": "City Clinic",
    "booking_for": "self"
  },
  "location": "City Clinic",
  "booking_for": "self"
}
```

---

## 4. ElevenLabs Configuration

1. **Tool Settings**: Set as **ASYNC** (fire-and-forget).
2. **Assignments**: Map response fields (e.g., `location`) to their corresponding dynamic variables (e.g., `{{location}}`).
