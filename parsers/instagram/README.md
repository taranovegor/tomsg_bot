# Instagram Parser

Extracts video (post / reel / carousel videos) from an Instagram link, with caption, author,
publish date and like / comment counters.

## Supported links
- `https://instagram.com/p/<id>/`
- `https://instagram.com/reel(s)/<id>/`
- `https://instagram.com/share/<id>/`

## Data source
[yt-dlp](https://github.com/yt-dlp/yt-dlp), used as a library (`extract_info(download=False)`).
The parser asks for a progressive mp4 (video + audio in one file), so no muxing is needed; the bot
downloads the CDN URL itself.

## Configuration
| Env               | Purpose                                                                    | Required |
|-------------------|----------------------------------------------------------------------------|----------|
| `INSTAGRAM_PROXY` | Proxy for yt-dlp requests to Instagram, e.g. `http://user:pass@host:3128`. | no       |

Only extraction goes through the proxy; media is downloaded from the CDN directly (CDN URLs are
not bound to the extracting IP).

## Registration
`@register("instagram")` → service key `parser_instagram`.

## Notes & limitations
- **Photo posts are not supported** — yt-dlp extracts video only. Photo-only posts and
  photo-only carousels raise `ParseError`; photo items of mixed carousels are skipped.
- Instagram breaks yt-dlp's extractor from time to time: bump `yt-dlp` in `requirements.txt` and
  rebuild the PyInstaller binary when extraction starts failing.
