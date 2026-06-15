# Reddit Comment Parser

Extracts a Reddit comment (author, text, metrics) from a comment link, using Reddit's OAuth2 API.

## Supported links
- `https://www.reddit.com/r/<sub>/comments/<post_id>/.../<comment_id>`
- short `reddit.com` share links (resolved via redirect)

## Data source
Reddit Data API: `https://www.reddit.com/api/v1/access_token` (OAuth2) and `.../api/info.json`.

## Configuration
| Env                         | Purpose                                                  | Required |
|-----------------------------|----------------------------------------------------------|----------|
| `REDDIT_CLIENT_ID`          | Application client ID.                                   | yes      |
| `REDDIT_CLIENT_SECRET`      | Application client secret.                               | yes      |
| `REDDIT_APP_OWNER_USERNAME` | Owner username, sent in the User-Agent (`by /u/<name>`). | yes      |

## Registration
`@register("reddit")` → service key `parser_reddit`.

## Notes & limitations
- HTML comment content is converted via `html_adapter.py`.

## Useful resources
- [Reddit API OAuth Documentation](https://www.reddit.com/dev/api/oauth/)
- [Reddit Data API Wiki](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki)
