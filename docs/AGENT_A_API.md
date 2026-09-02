# Agent A API

## GET /health

Public health endpoint.

## GET /property

Returns the current property profile embedded in the application.

## POST /agent/run

Protected by `X-Agent-Key`.

Body:

```json
{
  "campaign": "healthcare",
  "max_queries": 5
}
```

Campaign values:

- healthcare
- corporate
- relocation
- partners
- social

## GET /leads

Protected by `X-Agent-Key`.

Optional query parameters:

- `classification=HOT`
- `campaign=healthcare`
- `status=NEW`
- `min_score=80`

## GET /leads/hot

Returns score >= 90.

## POST /leads/{lead_id}/approve

Marks a lead as approved for contact. This endpoint does not send a message. It is an explicit approval state for a future outreach adapter.

## OpenAPI

When running locally:

`http://localhost:8000/docs`
