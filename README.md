# ReCollect Waste EU (Custom Component)

A modified fork of Home Assistant's built-in [ReCollect Waste](https://www.home-assistant.io/integrations/recollect_waste) integration (originally by [@bachya](https://github.com/bachya)), with a per-bin-type sensor pattern borrowed from [mampfes/hacs_waste_collection_schedule](https://github.com/mampfes/hacs_waste_collection_schedule).

## ⚠️ Full disclosure: this is vibe coded

This integration was built almost entirely through back-and-forth with an AI assistant (Claude), not written from scratch by a human who deeply understands the Home Assistant integration internals. Concretely, that means:

- The core structure (coordinator, config flow, calendar/sensor platforms) is lifted directly from the original `recollect_waste` core integration, with the domain renamed to `recollect_waste_eu` so it can run alongside the real one.
- The per-pickup-type sensor logic (one entity per bin type, discovered dynamically, styled after `waste_collection_schedule`'s approach so each bin gets its own icon and shows up cleanly in Favourites/dashboards) was designed and iterated on with AI assistance, not independently verified against Home Assistant's full entity lifecycle documentation.
- Several bugs shipped in early iterations of this repo purely from copy-paste/JSON errors (missing closing braces in `manifest.json` and `translations/en.json`, an invalid `requirements` string for a git dependency) that a more careful human review would likely have caught before they hit a running instance.
- Testing has been "install it on my own HAOS box and see what breaks," not unit tests, not CI, not a second pair of eyes.

**What this means for you if you use it:**
- Treat it as a personal/hobbyist project, not a production-grade or officially reviewed integration.
- Read the code before trusting it with anything you care about — it's not long, and it's not trying to hide anything.
- Expect rough edges. Pickup type icons/display names are hardcoded to a short list (`GeneralWaste`, `Garden`, `RecyclingwithFlex`) matching one specific ReCollect service area; if your bin types have different names, you'll want to extend `const.py` yourself.
- The `aiorecollect` dependency is pinned to a `dev` branch of a fork (`git+https://github.com/mechkey/aiorecollect.git@dev`), not a stable release — it can change underneath you without warning.
- PRs, issues, and "hey this is wrong" corrections are genuinely welcome. This project would benefit from actual scrutiny.

## What it does

- Sets up ReCollect Waste pickup data (place ID + service ID) same as the core integration.
- Provides a `calendar` entity showing all upcoming pickups.
- Provides `current_pickup` and `next_pickup` date sensors (from the original integration).
- Additionally creates **one sensor per distinct pickup type** (e.g. General Waste, Garden Waste, Recycling), each showing its own next collection date as its state and its own icon — designed so these can be added individually to a Home Assistant dashboard's Favourites/Sections view, the way `waste_collection_schedule` entities can.

## Installation

1. Copy `custom_components/recollect_waste_eu/` into your Home Assistant `config/custom_components/` folder (or install via HACS as a custom repository).
2. Restart Home Assistant.
3. Add the integration via **Settings → Devices & Services → Add Integration → ReCollect Waste EU**, entering your Place ID and Service ID.
4. Optionally enable "Use friendly names for pickup types" in the integration's options.

## Credit

- Original integration: [bachya/recollect_waste](https://github.com/bachya) (Home Assistant core).
- Per-type sensor pattern inspired by: [mampfes/hacs_waste_collection_schedule](https://github.com/mampfes/hacs_waste_collection_schedule).
- `aiorecollect` client: [mechkey/aiorecollect](https://github.com/mechkey/aiorecollect) (dev branch fork).
- Glue code, renaming, and the dynamic per-type sensor logic: assembled with AI assistance, as described above.
