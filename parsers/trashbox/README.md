# trashbox Parser

Extracts a comment (author, text, votes) from a trashbox.ru topic.

## Supported links
- trashbox.ru topic links containing a `#div_comment_<id>` anchor

## Data source
trashbox.ru endpoints: `/api_topics/<id>` and `/api_noauth.php?action=comments`.

## Configuration
Not required.

## Registration
`@register("trashbox")` → service key `parser_trashbox`.

## Notes & limitations
- trashbox.ru runs on the bobs.pro engine (shared with redspecial).
- Timestamps are normalized to UTC.
