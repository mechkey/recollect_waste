"""Support for ReCollect Waste sensors."""

from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util, slugify

from .const import (
    DEFAULT_PICKUP_ICON,
    LOGGER,
    PICKUP_TYPE_DISPLAY_NAMES,
    PICKUP_TYPE_ICONS,
)
from .coordinator import RecollectWasteConfigEntry, ReCollectWasteDataUpdateCoordinator
from .entity import ReCollectWasteEntity
from .util import async_get_pickup_type_names

ATTR_PICKUP_TYPES = "pickup_types"
ATTR_AREA_NAME = "area_name"

SENSOR_TYPE_CURRENT_PICKUP = "current_pickup"
SENSOR_TYPE_NEXT_PICKUP = "next_pickup"

SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key=SENSOR_TYPE_CURRENT_PICKUP,
        translation_key=SENSOR_TYPE_CURRENT_PICKUP,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_NEXT_PICKUP,
        translation_key=SENSOR_TYPE_NEXT_PICKUP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RecollectWasteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ReCollect Waste sensors based on a config entry."""
    coordinator = entry.runtime_data

    # The original two summary sensors (current/next pickup, whatever type).
    async_add_entities(
        ReCollectWasteSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )

    # One additional sensor per distinct pickup type, discovered dynamically
    # from the API data, so each bin type gets its own tile/icon/date.
    known_types: set[str] = set()

    @callback
    def _async_add_new_type_sensors() -> None:
        """Add a sensor for any pickup type not yet seen."""
        current_types: set[str] = set()
        for event in coordinator.data:
            current_types.update(
                async_get_pickup_type_names(entry, event.pickup_types)
            )

        new_types = current_types - known_types
        if not new_types:
            return

        known_types.update(new_types)
        async_add_entities(
            ReCollectWastePickupTypeSensor(coordinator, entry, pickup_type)
            for pickup_type in new_types
        )

    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_type_sensors))
    _async_add_new_type_sensors()


class ReCollectWasteSensor(ReCollectWasteEntity, SensorEntity):
    """Define the original current/next pickup summary sensors."""

    _attr_device_class = SensorDeviceClass.DATE

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

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
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

        super()._handle_coordinator_update()


class ReCollectWastePickupTypeSensor(ReCollectWasteEntity, SensorEntity):
    """Define a sensor showing the next date for a single pickup type."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: ReCollectWasteDataUpdateCoordinator,
        entry: RecollectWasteConfigEntry,
        pickup_type: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)

        self._pickup_type = pickup_type
        self._attr_unique_id = f"{self._identifier}_{slugify(pickup_type)}"
        self._attr_name = PICKUP_TYPE_DISPLAY_NAMES.get(pickup_type, pickup_type)
        self._attr_icon = PICKUP_TYPE_ICONS.get(pickup_type, DEFAULT_PICKUP_ICON)

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        today = dt_util.now().date()

        try:
            event = next(
                e
                for e in self.coordinator.data
                if e.date >= today
                and self._pickup_type
                in async_get_pickup_type_names(self._entry, e.pickup_types)
            )
        except StopIteration:
            LOGGER.debug("No upcoming pickup found for %s", self._pickup_type)
            self._attr_extra_state_attributes = {}
            self._attr_native_value = None
        else:
            self._attr_extra_state_attributes[ATTR_AREA_NAME] = event.area_name
            self._attr_native_value = event.date

        super()._handle_coordinator_update()
