# redspecial Parser

Extracts a comment (author, text, votes) from a redspecial.ru topic.

## Supported links
- redspecial.ru topic links containing a `#div_comment_<id>` anchor

## Data source
redspecial.ru endpoints: `/api_topics/<id>` and `/api_noauth.php?action=comments`.

## Configuration
Not required.

## Registration
`@register("redspecial")` → service key `parser_redspecial`.

## Notes & limitations
- redspecial.ru runs on the bobs.pro engine (shared with trashbox).
- Timestamps are normalized to UTC.
