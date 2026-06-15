# Twitter / X Parser

Extracts a tweet (text, media, author and engagement metrics) from a Twitter/X status link.

## Supported links
- `https://x.com/<user>/status/<id>`
- `https://twitter.com/<user>/status/<id>`

## Data source
[vxtwitter](https://github.com/dylanpdx/BetterTwitFix) public API:
`https://api.vxtwitter.com/status/<id>`. No authentication.

## Configuration
Not required.

## Registration
`@register("twitter")` → service key `parser_twitter`.

## Notes & limitations
- Timestamps are normalized to UTC.
