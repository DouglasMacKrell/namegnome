# TV Test Expectations

This document describes the expected scan results for each test directory in `tests/mocks/tv`, based on canonical logic from SCAN.md and the real test files present. Use this as a reference for regression and edge-case validation.

---

## Danger Mouse 2015 (Non-Anthology)
- **Mode:** Standard (no `--anthology`)
- **Expectation:**
  - Each file represents a single episode.
  - The episode number and title should be matched exactly to the canonical episode list.
  - No multi-episode spans or anthology logic should be triggered.
  - EDGE CASE: There are 2 series called Danger Mouse. One from 1981, and a more modern series from 2015. In this case, the year is passed in the directory and only some of the internal files. 
  - TVDB Reference 
    - Season 1: https://www.thetvdb.com/series/danger-mouse-2015/seasons/official/1
    - Season 2: https://www.thetvdb.com/series/danger-mouse-2015/seasons/official/2
- **Files:**
  - `Danger Mouse 2015-S01E01-Danger Mouse Begins Again.mp4` → S01E01, "Danger Mouse Begins Again"
  - `Danger Mouse 2015-S01E02-Danger At C Level.mp4` → S01E02, "Danger At C Level"
  - `Danger Mouse 2015-S01E03-Greenfinger.mp4` → S01E03, "Greenfinger"
  - `Danger Mouse 2015-S01E04-Planet Of The Toilets.mp4` → S01E04, "Planet Of The Toilets"
  - `Danger Mouse 2015-S02E49-The World Is Full Of Stuff.mp4` → S02E49, "The World Is Full Of Stuff"
  - `Danger Mouse-S02E38-A Fear To Remember.mp4` → S02E38, "A Fear To Remember"
  - `Danger Mouse-S02E39-Melted.mp4` → S02E39, "Melted"
  - `Danger Mouse-S02E42-Danger Thon.mp4` → S02E42, "Danger Thon"

---

## Firebuds (Anthology)
- **Mode:** `--anthology`
- **Expectation:**
  - Each file may contain one or more consecutive episodes (span), based on the segment titles.
  - The scan should split the filename on segment boundaries and match each to the canonical episode list.
  - Multi-episode spans (e.g., S01E01-E02) are allowed and expected.
  - EDGE CASE: Currently TVDB API lists all episodes in Season 2 and returns empty for Season 1
  - TVDB Reference
    - Season 1: https://www.thetvdb.com/series/firebuds/seasons/official/1
    - Season 2: https://www.thetvdb.com/series/firebuds/seasons/official/2
- **Files:**
  - `Firebuds-S01E01-Car In A Tree Dalmatian Day.mp4` → S01E01-E02, "Car In A Tree & Dalmatian Day"
  - `Firebuds-S01E02-Hubcap Heist Food Truck Fiasco.mp4` → S01E03-E04, "Hubcap Heist & Food Truck Fiasco"
  - `Firebuds-S01E03-Treehouse Trouble The Getaway Car That Got Away.mp4` → S01E05-E06, "Treehouse Trouble & The Getaway Car That Got Away"
  - `Firebuds-S02E20-The Camp Fire.mp4` → S02E38, "The Camp Fire"
  - `Firebuds-S02E21-The Haunted Hq All Souls Surprise.mp4` → S02E39-E40, "The Haunted Hq & All Souls Surprise"
  - `Firebuds-S02E22-Bamboozled Bo Food In A Flash.mp4` → S02E41-E42, "Bamboozled Bo & Food In A Flash"

---

## Martha Speaks (Anthology)
- **Mode:** `--anthology`
- **Expectation:**
  - Each file may contain one or more consecutive episodes (span), based on the segment titles.
  - The scan should split the filename on segment boundaries and match each to the canonical episode list.
  - Multi-episode spans (e.g., S01E01-E02) are allowed and expected.
  - EDGE CASE: Anthology series where the first episode shares it's name with the series. We also have an oddly formatted apostrophies for posessive "S" and "We Re"
  - TVDB Reference
    - Season 1: https://www.thetvdb.com/series/martha-speaks/seasons/official/1
    - Season 6: https://www.thetvdb.com/series/martha-speaks/seasons/official/6
- **Files:**
  - `Martha Speaks-S01E01-Martha Speaks Martha Gives Advice.mp4` → S01E01-E02, "Martha Speaks & Martha Gives Advice"
  - `Martha Speaks-S01E02-Martha And Skits Martha Plays A Part.mp4` → S01E03-E04, "Martha And Skits & Martha Plays A Part"
  - `Martha Speaks-S01E03-Martha Takes The Cake Codename Martha.mp4` → S01E05-E06, "Martha Takes The Cake & Codename Martha"
  - `Martha Speaks-S06E06-Tomato You Say Martha Questions.mp4` → S06E09-E10, "Tomato You Say & Martha Questions"
  - `Martha Speaks-S06E07-Martha S Sweater The Mystery Of The Missing Dinosaur.mp4` → S06E15-E16, "Marthas Sweater & The Mystery Of The Missing Dinosaur"
  - `Martha Speaks-S06E08-Martha S Holiday Surprise We Re Powerless.mp4` → S06E13-E14, "Marthas Holiday Surprise & Were Powerless"

---

## Paw Patrol (Anthology)
- **Mode:** `--anthology`
- **Expectation:**
  - Each file may contain one or more consecutive episodes (span), based on the segment titles.
  - The scan should split the filename on segment boundaries and match each to the canonical episode list.
  - Multi-episode spans (e.g., S01E01-E02) are allowed and expected.
  - EDGE CASES
    - The API returns "Pups and the Kitty-tastrophe" which we need to match to "Pups And The Kitty Tastrophe"
    - The API returns "Pups Save the Chili Cook-Off" which we need to match to "Pups Save A Chili Cook Out"
    - Season 7 has prefixes/monikers before titles. "Mighty Pups, Charged Up: Pups Stop a Humdinger Horde" and "Mighty Pups, Charged Up: Pups Save a Mighty Lighthouse" need to find a match when the input truncates titles to "Mighty Pups Charged Up Pups Stop A Humdinger Horde Pups Save A Mighty Lighthouse"
    - The file for Season 8 Episode 7 is a double length segment and only contains 1 episode
  - TVDB References
    - Season 1: https://www.thetvdb.com/series/paw-patrol/seasons/official/1
    - Season 2: https://www.thetvdb.com/series/paw-patrol/seasons/official/2
    - Season 3: https://www.thetvdb.com/series/paw-patrol/seasons/official/3
    - Season 4: https://www.thetvdb.com/series/paw-patrol/seasons/official/4
    - Season 5: https://www.thetvdb.com/series/paw-patrol/seasons/official/5
    - Season 6: https://www.thetvdb.com/series/paw-patrol/seasons/official/6
    - Season 7: https://www.thetvdb.com/series/paw-patrol/seasons/official/7
    - Season 8: https://www.thetvdb.com/series/paw-patrol/seasons/official/8
- **Files:**
  - `Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4` → S01E05-E06, "Pups And The Kitty Tastrophe & Pups Save A Train"
  - `Paw Patrol-S02E01-Pups Save The Space Alien Pups Save A Flying Frog.mp4` → S02E05-E06, "Pups Save The Space Alien & Pups Save A Flying Frog"
  - `Paw Patrol-S03E01-Pups Find A Genie Pups Save A Tightrope Walker.mp4` → S03E01-E02, "Pups Find A Genie & Pups Save A Tightrope Walker"
  - `Paw Patrol-S04E01-Pups Save A Blimp Pups Save A Chili Cook Out.mp4` → S04E01-E02, "Pups Save A Blimp & Pups Save The Chili Cook Off"
  - `Paw Patrol-S05E01-Pups Save The Kitty Rescue Crew Pups Save An Ostrich.mp4` → S05E01-E02, "Pups Save The Kitty Rescue Crew & Pups Save An Ostrich"
  - `Paw Patrol-S06E01-Pups Save The Jungle Penguins Pups Save A Freighter.mp4` → S06E01-E02, "Pups Save The Jungle Penguins & Pups Save A Freighter"
  - `Paw Patrol-S07E01-Mighty Pups Charged Up Pups Stop A Humdinger Horde Pups Save A Mighty Lighthouse.mp4` → S07E01-E02, "Mighty Pups Charged Up Pups Stop A Humdinger Horde & Mighty Pups Charged Up Pups Save A Mighty Lighthouse"
  - `Paw Patrol-S08E01-Pups Save A Runaway Rooster Pups Save A Snowbound Cow.mp4` → S08E01-E02, "Pups Save A Runaway Rooster & Pups Save A Snowbound Cow"
  - `Paw Patrol-S08E04-Pups Stop The Cheetah.mp4` → S08E07, "Pups Stop The Cheetah"

---

*All expectations are based on canonical scan logic as described in SCAN.md. Edge cases and ambiguous files should be flagged as manual if the segment cannot be confidently matched to the canonical episode list.*
