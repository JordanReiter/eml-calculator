# Contract: `config.toml`

**Last updated**: 2026-11-17 (link titles added alongside URLs; video URL supplied)

## Purpose
Source-controlled, generation-time configuration for page link titles and URLs (FR-017, FR-018). Read by the CLI during output generation. Not fetched over the network and not constructed at runtime.

## Location
Repository root: `config.toml` (or the documented path resolved at generation time; literals remain in this file).

## Schema

```toml
# Literal link titles and URLs only.
paper_title = "the paper"
paper_url = "https://arxiv.org/abs/2603.21852"

video_title = "the video"
video_url = "https://www.youtube.com/watch?v=LxVW3b8jVdE"
```

### Keys
- **`paper_title`** (string, required): Link text for the paper anchor.
- **`paper_url`** (string, required): Literal URL for the paper anchor. Must be `https://arxiv.org/abs/2603.21852` for this feature as specified.
- **`video_title`** (string, required when `video_url` is present): Link text for the video anchor.
- **`video_url`** (string, optional): Literal URL for the video anchor. When missing or an empty value, the generated page MUST omit the video anchor entirely and show no placeholder/empty href. A `video_url` without a `video_title` is a generation error.

## Rendering rules (consumed by HTML generator)
- Citation text is fixed in source: `Odrzywołek, *All elementary functions from a single binary operator*, arXiv:2603.21852v2`.
- Anchor 1: text = `paper_title`, href = `paper_url`.
- Anchor 2 (only if both video keys are configured): text = `video_title`, href = `video_url`.
- Explanation is fixed in source (2–3 sentences); it is not configurable.
- No other anchors appear on the page (FR-017, SC-007).

## Validation / error handling
- Missing or unreadable config, invalid TOML, missing required `paper_title`/`paper_url`, or a video URL without a title is a user-facing generation error (boundary failure) with a clear message.
- Values are treated as literals and inserted into HTML with proper escaping; they are never executed or fetched.
