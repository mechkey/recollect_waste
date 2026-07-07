"""Define ReCollect Waste constants."""

import logging

DOMAIN = "recollect_waste_eu"

LOGGER = logging.getLogger(__package__)

CONF_PLACE_ID = "place_id"
CONF_SERVICE_ID = "service_id"

# Icons and friendlier display names for known pickup types. Add more entries
# here as new pickup type names appear in your ReCollect data; anything not
# listed falls back to DEFAULT_PICKUP_ICON and its raw API name.
PICKUP_TYPE_ICONS = {
    "GeneralWaste": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "RecyclingwithFlex": "mdi:recycle",
}
DEFAULT_PICKUP_ICON = "mdi:trash-can-outline"

PICKUP_TYPE_DISPLAY_NAMES = {
    "GeneralWaste": "General Waste",
    "Garden": "Garden Waste",
    "RecyclingwithFlex": "Recycling",
}
