# TikTok Parser

Extracts a TikTok video from short or full video links.

## Supported links
- `https://(vm|vt).tiktok.com/<id>` (short, resolved via redirect)
- `https://(www.|m.)tiktok.com/@<user>/video/<id>`

## Data source
Short links are resolved with an HTTP redirect; the video and thumbnail URLs are built from
the configured resource templates.

## Configuration
| Env                             | Purpose                                            | Required |
|---------------------------------|----------------------------------------------------|----------|
| `TIKTOK_VIDEO_RESOURCE_URL`     | URL template for the video file (`%s` = video ID). | yes      |
| `TIKTOK_THUMBNAIL_RESOURCE_URL` | URL template for the thumbnail (`%s` = video ID).  | yes      |

## Registration
`@register("tiktok")` → service key `parser_tiktok`.

## Notes & limitations
- Relies on external resource templates rather than the official TikTok API.
