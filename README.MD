# Prayer Times Calculator - Offline

Not designed as a general purpose prayer time library. This is meant as a cloud-free, drop-in replacement for [`prayer-times-calculator`](https://github.com/uchagani/prayer-times-calculator), which in turn is used by the [Islamic Prayer Times HomeAssistant integration](https://www.home-assistant.io/integrations/islamic_prayer_times/).


Equivalence to the `prayer-times-calculator` library was checked by emperical comparison of 50,000 requests (each with randomized parameters). The original intention was to replicate the output exactly, however please note the following exceptions where `prayer-times-calculator-offline` will return a different result than `prayer-times-calculator` for the same call:

* Asr calculation is stable; at time of writing, AlAdhan's API uses the [API server's local time](https://github.com/islamic-network/prayer-times/blob/f7ed3a2467fbced252a0914c8b202c8b61ca58b9/src/PrayerTimes/PrayerTimes.php#L538) as part of the Asr calculation, causing the returned time to drift as the server's day progresses.
* ISO8601 date components are correct; at time of writing, AlAdhan's API sometime returns ISO8601 timestamps with correct times but incorrect dates.
  * E.g. [this API call](https://api.aladhan.com/v1/timings/28-06-2042?latitude=78.76131061889032&longitude=72.35356426766558&method=21&iso8601=true&school=1&midnightMode=1&latitudeAdjustmentMethod=3&tune=1%2C3%2C-1%2C5%2C4%2C4%2C-2%2C-2%2C1) where all timestamps are returned with the same date component, making Isha appear to happen before Maghrib and Fajr appear to happen after Sunrise
* Portugal Maghrib tuning applied correctly; At time of writing, AlAdhan's API maps the [Asr tuning value to Maghrib](https://github.com/islamic-network/api.aladhan.com/blob/f3d57f7c7b54f5bb9592efdb984fbbea41093f82/api/Utils/PrayerTimesHelper.php#L306)
* Local time output (`iso8601=False`) is not supported, as it is not required for use in HomeAssistant (which deals only with UTC internally)
* 'None' is supported as a high-latitude adjustment method
* Angles of 0 are supported for the "custom" calculation method; at time of writing, AlAdhan's API silently ignores such angles and uses a different default angle in their place.
* Floating point computations take place on your CPU, which may vary from the AlAdhan API server's CPU; there may be 1-minute differences if these computational variations span a rounding break. Hijri date calculation may also be affected, including the 30-minute Isha offset during Ramadan when using the Makkah calculation method.


*The remainder of this README is based on that from prayer-times-calculator.*

## Usage

Please refer to the [usage section of `prayer-times-calculator`](https://github.com/uchagani/prayer-times-calculator?tab=readme-ov-file#usage).
