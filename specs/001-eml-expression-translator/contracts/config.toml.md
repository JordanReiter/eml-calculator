# Contract: `config.toml`

**Last updated**: 2026-11-19 (four keys unchanged; link text has no fixed sample literal; header content moved to `top_fragment.html`)

## Purpose
Source-controlled, generation-time configuration for page link titles and URLs only (FR-017, FR-018). Literal page-top H1, summary, "References" heading, and Article/Video label markup are owned by the root `top_fragment.html`, not by this file. Read by the CLI during output generation. Not fetched over the network and not constructed at runtime.

## Location
Repository root: `config.toml` (or the documented path resolved at generation time; literals remain in this file).

## Schema

```toml
# Literal link titles and URLs only. Values below are examples, not required literals.
# paper_title is a plain string; it may include the author name and article title.
paper_title = "Odrzywołek, All elementary functions from a single binary operator"
paper_url = "https://arxiv.org/abs/2603.21852"

video_title = "the video"
video_url = "https://www.youtube.com/watch?v=LxVW3b8jVdE"
```

### Keys
- **`paper_title`** (string, required): Link text for the paper anchor. It is a plain string that may contain the author name and the article title; no fixed sample literal (e.g. `the paper`) is required, and the renderer adds no styling such as `<em>`.
- **`paper_url`** (string, required): Literal URL for the paper anchor, supplied by the owner; no default or enforced value.
- **`video_title`** (string, optional): Link text for the video anchor; substitutes as an empty string when absent.
- **`video_url`** (string, optional): Literal URL for the video anchor. When missing or empty, an empty string is substituted into the fragment; no generation error is raised and the renderer performs no row omission. The owner-authored fragment determines the rendered result.

## Rendering rules (consumed by HTML generator)
- Page-top H1, summary paragraph, "References" heading, and Article/Video label markup come from the source-controlled root `top_fragment.html`, not from this file or Python constants. The separate fixed citation paragraph is removed.
- Anchor 1 (Article row): text = `paper_title` as a plain string (may include author name and article title, rendered without added styling), href = `paper_url`.
- Anchor 2 (Video row): text = substituted `video_title`, href = substituted `video_url` (empty strings when absent).
- Summary/explanation text comes from `top_fragment.html`; it is not configurable here.
- No other anchors appear on the page (FR-017, SC-007).

## Validation / error handling
- Missing or unreadable config, invalid TOML, or missing required `paper_title`/`paper_url` is a user-facing generation error (boundary failure) with a clear message. Absent optional video keys are not an error.
- Values are treated as literals and inserted into HTML with proper escaping; they are never executed or fetched.
