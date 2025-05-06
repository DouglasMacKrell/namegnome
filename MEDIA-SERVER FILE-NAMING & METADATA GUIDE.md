# Media‑Server File‑Naming & Metadata Guide

> **Quick take:** Video‑first servers (Plex‑style scanners) demand precise filenames & folder structures; music‑first/DLNA servers mainly read embedded tags; channel builders inherit whatever their upstream library already has. Keep movies as `Movie Name (Year)/Movie Name (Year).ext`, TV as `Show/Season ##/Show ‑ S01E01.ext`, and tag your audio—then everything here works.

---

## 1 · Full‑featured video servers (Plex‑style scanners)

| Server       | Movies                                                    | TV Episodes                                      | Music                                  |
| ------------ | --------------------------------------------------------- | ------------------------------------------------ | -------------------------------------- |
| **Emby**     | `Movie (2019)/Movie (2019).mkv`                           | `Show (2010)/Season 01/Show – S01E01.mkv`        | Reads ID3/FLAC tags; filename optional |
| **Jellyfin** | Same as Emby; `{tmdb‑id}` / `{imdb‑id}` allowed in folder | Same + `[tvdbid‑xxxx]` or `[tmdbid‑xxxx]`        | Tags preferred                         |
| **Kodi**     | `Movie Name (Year)/Movie Name (Year).ext`                 | `Show Name (Year)` → `S01E01` or `1x01` variants | Tags; optional `album.nfo`             |
| **Olaris**   | Mirrors Plex/Emby spec                                    | Mirrors Plex/Emby spec                           | Tags                                   |
| **Streama**  | Parses `Movie (Year)` but you can edit manually           | Same; manual edits                               | —                                      |

### Key rule

If it works in Plex, it works everywhere in this family.

---

## 2 · Lightweight DLNA / UPnP servers

* **Universal Media Server** – shows folder tree; will *attempt* `Show – S01E01`, but metadata comes from tags.
* **Gerbera** – Ignores filenames; maps DLNA fields from embedded metadata.
* **ReadyMedia / MiniDLNA** – Uses embedded tags first, filename only as fallback.

> **Tag hygiene is king**—filenames here only shape the folder view.

---

## 3 · Music‑centric servers

| Server        | What they read first                | Filename influence                  |
| ------------- | ----------------------------------- | ----------------------------------- |
| **Navidrome** | ID3/FLAC/OGG tags (Subsonic API)    | None; folder view optional          |
| **Ampache**   | Tags; user‑defined pattern fallback | Helps when tags are missing         |
| **Polaris**   | Tag‑only library                    | Ignored unless browsing raw folders |

---

## 4 · Channel builders & speciality libraries

* **dizqueTV / Tunarr** – inherit metadata from Plex/Jellyfin; no naming rules.
* **Stash** – Uses perceptual hashes; filenames irrelevant.
* **MediaGoblin** – Each upload is a standalone object; titles entered by user.

---

## 5 · One‑size‑fits‑most patterns

```text
Movies/
  Movie Title (2023)/
    Movie Title (2023).mkv

TV/
  Show Title (2011)/
    Season 01/
      Show Title - S01E01 - Optional Title.ext

Music/
  Artist/
    Album (Year)/
      01 Track Title.ext  ← ID3 / FLAC tags filled in
```

---

## 6 · Practical tips

1. **Embed provider IDs** in folder names (`{tmdb-12345}`) when titles clash.
2. **Avoid special characters** that break Windows/macOS (`: * ? " < > |`).
3. **Tag first, then rename** for audio; use MusicBrainz Picard or `beets`.
4. **Fix once, reap everywhere:** Channel builders & DLNA share whatever Jellyfin/Plex already resolved.
5. **For DLNA TVs** that ignore tags, strip bad ID3 so filename becomes display title.

---

## 6 · Edge Cases & Advanced Patterns

* **Anthology or two‑story episodes** – If a single file contains more than one broadcast segment, name it `Show – S01E01-E02.ext`; Plex/Emby/Jellyfin create two episode entries that point to the same file. ([support.plex.tv](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/?utm_source=chatgpt.com))
* **Anthology shows with separate segment files** – Split the recording and name each part individually (`S01E01`, `S01E02`) following the provider’s episode list on TheTVDB. ([reddit.com](https://www.reddit.com/r/PleX/comments/bh306k/what_is_the_best_way_to_fix_this_the_episodes/?utm_source=chatgpt.com))
* **Specials & bonus content** – Place them in a `Season 00` or `Specials` folder and name `Show – S00E13 – Title.ext`. ([reddit.com](https://www.reddit.com/r/PleX/comments/r68h8h/how_to_include_specials/?utm_source=chatgpt.com))
* **Date‑based episodes (daily news, talk shows, livestreams)** – Use `Show – YYYY-MM-DD.ext`; if multiple episodes air the same day, add a letter suffix (`YYYY-MM-DDa`). ([reddit.com](https://www.reddit.com/r/PleX/comments/12alhj1/datebased_tv_episodes_with_two_from_the_same_day/?utm_source=chatgpt.com))
* **Absolute numbering for long‑running anime** – Jellyfin/Plex don’t support `S01E367`; instead, reset season/episode per provider list and keep the absolute number in optional info (e.g., `S17E01 [Ep367]`). ([forum.jellyfin.org](https://forum.jellyfin.org/t-absolute-numbering-for-anime?utm_source=chatgpt.com))
* **Multiple editions / cuts of a movie** – Keep all versions in the movie folder and suffix the filename: `Movie (2023) - Director's Cut.mkv`, `Movie (2023) - 4K Version.mkv`. Plex auto‑groups editions; Emby shows selectable labels. ([support.plex.tv](https://support.plex.tv/articles/multiple-editions/?utm_source=chatgpt.com), [emby.media](https://emby.media/community/index.php?%2Ftopic%2F121322-multiple-version-custom-naming%2F=&utm_source=chatgpt.com))
* **Multi‑resolution or codec variants** – Likewise, add `- 1080p`, `- 4K HDR`, `- HEVC` to help Plex/Emby pick the best copy for the device. ([support.plex.tv](https://support.plex.tv/articles/multiple-editions/?utm_source=chatgpt.com))
* **Provider ID overrides** – Append `{tvdb-12345}` or `{tmdb-56789}` (square or curly braces) to the series or movie folder when titles are ambiguous. Supported by Jellyfin, Plex and Emby. ([features.jellyfin.org](https://features.jellyfin.org/posts/1671/parse-tvdb-ids-in-series-folder-name?utm_source=chatgpt.com), [youtube.com](https://www.youtube.com/watch?v=zClNv4_mSd0&utm_source=chatgpt.com))
* **Extras, trailers & featurettes** – Store alongside the movie using `MovieName (Year)/MovieName (Year) - Description-Extra_Type.ext` or inside `Extras/`. Recognised `-trailer`, `-behindthescenes`, `-interview`, etc. suffixes let Plex surface them. ([support.plex.tv](https://support.plex.tv/articles/local-files-for-trailers-and-extras/?utm_source=chatgpt.com))

### 6.1 Example

Anthology Show: Paw Patrol

INPUT:
`Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4`
`Paw Patrol-S01E02-Pup Pup Boogie Pups In A Fog.mp4`
`Paw Patrol-S01E03-Pups Save The Sea Turtles Pup And The Very Big Baby.mp4`

OUTPUT:
`Paw Patrol - S01E01-E02 - Pups And The Kitty-tastrophe & Pups Save A Train.mp4`
`Paw Patrol - S01E03-E04 - Pup Pup Boogie & Pups In A Fog.mp4`
`Paw Patrol - S01E05-E06 - Pups Save The Sea Turtles & Pup And The Very Big Baby.mp4`

As you can see:
- Original episode numbering should be lowered in priority, and episode names should take high priority.
- Episode names will need to be parsed and correctly separated by an "&".
- Single file episode numbering spans applied as per convention.

In edge cases where we only get episode numbers and no episode names or seemingly correctly numbered and named individual episodes with an incremental count, but --anthology is passed, we need to query the show and cross-check the expected number of episodes from the response with how many episodes from that season are included in the target directory. If the number of files in the directory is roughly half the expected number of episodes from the API response, then we can safely assume the episodes are in the right order, and that NameGnome can override the existing file numbering and naming to make each episode an incremental two episode span (like in the Paw Patrol example above)

—

*Last updated: 2025‑05‑06*
