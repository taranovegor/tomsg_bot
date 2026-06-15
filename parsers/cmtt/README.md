# CMTT Comment Parser (DTF / vc.ru)

Extracts a comment (author, text, reactions) from DTF or vc.ru — both built on the CMTT platform.

## Supported links
- `https://dtf.ru/<...>?comment=<id>`
- `https://vc.ru/<...>?comment=<id>`

## Data source
CMTT API: `https://api.<domain>/v2.5/comments?commentId=<id>`. No authentication.

## Configuration
Not required.

## Registration
`@register("cmtt")` → service key `parser_cmtt`.

## Notes & limitations
- Only `https` links are supported.
- Timestamps are normalized to UTC.
