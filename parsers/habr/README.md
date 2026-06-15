# Habr Comment Parser

Extracts a comment (author, text) from a Habr article thread.

## Supported links
- `https://habr.com/<...>/<article_id>...#comment_<comment_id>`

## Data source
Habr internal API: `https://habr.com/kek/v2/articles/<id>/...`. No authentication.

## Configuration
Not required.

## Registration
`@register("habr")` → service key `parser_habr`.

## Notes & limitations
- Images inside a comment are rendered as links (`html_processor.py`).
- Timestamps are normalized to UTC.
