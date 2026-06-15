# Truth Social Parser

Extracts a Truth Social status (text, media, metrics).

## Supported links
- `https://truthsocial.com/@<user>/posts/<id>`
- `https://truthsocial.com/@<user>/<id>`

## Data source
Truth Social API: `https://truthsocial.com/api/v1/statuses/<id>`. No authentication.

## Configuration
Not required.

## Registration
`@register("truthsocial")` → service key `parser_truthsocial`.

## Notes & limitations
- Sends a browser-like User-Agent (the endpoint rejects generic agents).
- Timestamps are normalized to UTC.
