# YouTube Comment Parser

Extracts a YouTube comment (author, text, metrics) from a watch link that points to a comment.

## Supported links
- `https://www.youtube.com/watch?v=<id>&lc=<comment_id>`
- `https://youtu.be/<id>?lc=<comment_id>`

## Data source
YouTube Data API v3: `https://youtube.googleapis.com/youtube/v3/comments`.

## Configuration
| Env               | Purpose                           | Required |
|-------------------|-----------------------------------|----------|
| `YOUTUBE_API_KEY` | API key for the YouTube Data API. | yes      |

## Registration
`@register("youtube")` → service key `parser_youtube`.

## Notes & limitations
- Timestamps are normalized to UTC.
