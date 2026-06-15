# Instagram Parser

Extracts media (photo / video) from an Instagram post, reel or share link.

## Supported links
- `https://instagram.com/p/<id>/`
- `https://instagram.com/reel(s)/<id>/`
- `https://instagram.com/share/<id>/`

## Data source
A self-hosted Instagram parser service (see `INSTAGRAM_VIDEO_PARSER_URL`). The target URL is
encrypted and passed to the service in the `Url` request header.

## Configuration
| Env                          | Purpose                                          | Required |
|------------------------------|--------------------------------------------------|----------|
| `INSTAGRAM_VIDEO_PARSER_URL` | Address of the parser service.                   | yes      |
| `INSTAGRAM_ENCRYPTION_KEY`   | Key used to encrypt the URL sent to the service. | yes      |

## Registration
`@register("instagram")` → service key `parser_instagram`.

## Notes & limitations
- The URL is encrypted with AES-ECB (`cipher.py`); ECB is a weak mode, tolerable here only
  because the payload is a public URL.
