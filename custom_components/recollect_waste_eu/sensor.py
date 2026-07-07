"""Support for ReCollect Waste sensors."""

from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import LOGGER
from .coordinator import RecollectWasteConfigEntry, ReCollectWasteDataUpdateCoordinator
from .entity import ReCollectWasteEntity
from .util import async_get_pickup_type_names

ATTR_PICKUP_TYPES = "pickup_types"
ATTR_AREA_NAME = "area_name"
ATTR_UPCOMING_PICKUPS = "upcoming_pickups"

SENSOR_TYPE_CURRENT_PICKUP = "current_pickup"
SENSOR_TYPE_NEXT_PICKUP = "next_pickup"
SENSOR_TYPE_UPCOMING = "upcoming_pickups"

SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key=SENSOR_TYPE_CURRENT_PICKUP,
        translation_key=SENSOR_TYPE_CURRENT_PICKUP,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_NEXT_PICKUP,
        translation_key=SENSOR_TYPE_NEXT_PICKUP,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_UPCOMING,
        translation_key=SENSOR_TYPE_UPCOMING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RecollectWasteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ReCollect Waste sensors based on a config entry."""
    async_add_entities(
        ReCollectWasteSensor(entry.runtime_data, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class ReCollectWasteSensor(ReCollectWasteEntity, SensorEntity):
    """Define a ReCollect Waste sensor."""

    PICKUP_INDEX_MAP = {
        SENSOR_TYPE_CURRENT_PICKUP: 1,
        SENSOR_TYPE_NEXT_PICKUP: 2,
    }

    def __init__(
        self,
        coordinator: ReCollectWasteDataUpdateCoordinator,
        entry: RecollectWasteConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)

        self._attr_unique_id = f"{self._identifier}_{description.key}"
        self.entity_description = description

        # The upcoming_pickups sensor's state is a count, not a date, so it
        # shouldn't use the DATE device class that the other two sensors use.
        if description.key != SENSOR_TYPE_UPCOMING:
            self._attr_device_class = SensorDeviceClass.DATE

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.key == SENSOR_TYPE_UPCOMING:
            self._handle_upcoming_update()
        else:
            self._handle_single_pickup_update()

        super()._handle_coordinator_update()

    @callback
    def _handle_upcoming_update(self) -> None:
        """Compute the next occurrence date for each distinct pickup type."""
        today = dt_util.now().date()
        seen_types: dict[str, dict] = {}

        for event in self.coordinator.data:
            if event.date < today:
                continue
            for pickup_type in async_get_pickup_type_names(
                self._entry, event.pickup_types
            ):
                if pickup_type not in seen_types:
                    seen_types[pickup_type] = {
                        "type": pickup_type,
                        "date": event.date.isoformat(),
                        "days": (event.date - today).days,
                    }

        upcoming = sorted(seen_types.values(), key=lambda x: x["days"])
        self._attr_extra_state_attributes = {ATTR_UPCOMING_PICKUPS: upcoming}
        self._attr_native_value = len(upcoming)

    @callback
    def _handle_single_pickup_update(self) -> None:
        """Handle the existing current/next pickup sensors."""
        relevant_events = (
            e for e in self.coordinator.data if e.date >= dt_util.now().date()
        )
        pickup_index = self.PICKUP_INDEX_MAP[self.entity_description.key]

        try:
            for _ in range(pickup_index):
                event = next(relevant_events)
        except StopIteration:
            LOGGER.debug("No pickup event found for %s", self.entity_description.key)
            self._attr_extra_state_attributes = {}
            self._attr_native_value = None
        else:
            self._attr_extra_state_attributes[ATTR_AREA_NAME] = event.area_name
            self._attr_extra_state_attributes[ATTR_PICKUP_TYPES] = (
                async_get_pickup_type_names(self._entry, event.pickup_types)
            )
            self._attr_native_value = event.date
