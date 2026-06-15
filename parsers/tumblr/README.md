# Tumblr Parser

Extracts media (photos / videos) and text from a Tumblr post.

## Supported links
- `https://<blog>.tumblr.com/post/<id>`
- `https://www.tumblr.com/<blog>/<id>`

## Data source
Tumblr API v2: `https://api.tumblr.com/v2/blog/<blog>.tumblr.com/posts`.

## Configuration
| Env              | Purpose                               | Required |
|------------------|---------------------------------------|----------|
| `TUMBLR_API_KEY` | API key from your Tumblr application. | yes      |

## Registration
`@register("tumblr")` → service key `parser_tumblr`.

## Notes & limitations
- None.
