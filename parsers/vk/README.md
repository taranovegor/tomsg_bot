# VK / OK Clips Parser

Extracts a VK or OK (Odnoklassniki) clip as a video.

## Supported links
- `https://vk.com/clip...` / `https://vk.com/clips...`
- `https://ok.ru/clip?owner_id=...`

## Data source
Clip identifiers are derived from the URL; a static thumbnail is used for the result.

## Configuration
| Env                | Purpose                              | Required |
|--------------------|--------------------------------------|----------|
| `VK_THUMBNAIL_URL` | Static thumbnail URL used for clips. | yes      |

## Registration
`@register("vk")` → service key `parser_vk`.

## Notes & limitations
- Handles both vk.com and ok.ru clip links.
