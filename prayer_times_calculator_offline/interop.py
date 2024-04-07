"""Prayer times calculator api."""
from __future__ import annotations

from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
import enum
import math
import typing

from .exceptions import CalculationMethodError
from .methods import CALCULATION_METHODS
from .praytimes import PrayTimes  # type: ignore


class School(enum.Enum):
    SHAFI = "shafi"
    HANAFI = "hanafi"


class MidnightMode(enum.Enum):
    STANDARD = "standard"
    JAFARI = "jafari"


class HighLatitudeAdjustmentMethod(enum.Enum):
    NONE = "none"
    MIDDLE_OF_NIGHT = "middle of the night"
    ONE_SEVENTH = "one seventh"
    ANGLE_BASED = "angle based"


class PrayerTimesCalculator:
    """Prayer time calculator class."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        calculation_method: str,
        date: str,
        school: str = School.SHAFI.value,
        midnightMode: str = MidnightMode.STANDARD.value,
        latitudeAdjustmentMethod: str = HighLatitudeAdjustmentMethod.NONE.value,
        tune: bool = False,
        imsak_tune: float = 0,
        fajr_tune: float = 0,
        sunrise_tune: float = 0,
        dhuhr_tune: float = 0,
        asr_tune: float = 0,
        maghrib_tune: float = 0,
        sunset_tune: float = 0,
        isha_tune: float = 0,
        midnight_tune: float = 0,
        fajr_angle: float | int | None = None,
        maghrib_angle: float | int | None = None,
        isha_angle: float | int | None = None,
        shafaq: str = "general",
        iso8601: bool = True,
    ) -> None:
        self._calculation_parameters = {}
        try:
            method_parameters = CALCULATION_METHODS[calculation_method.lower()]
            self._calculation_parameters.update(method_parameters)
        except KeyError:
            raise CalculationMethodError(calculation_method, list(CALCULATION_METHODS))

        try:
            self._school = School(school.lower())
        except ValueError:
            raise CalculationMethodError(school, list(x.value for x in School))

        try:
            self._midnight_mode = MidnightMode(midnightMode.lower())
        except ValueError:
            raise CalculationMethodError(
                midnightMode, list(x.value for x in MidnightMode)
            )

        try:
            self._lat_adj_method = HighLatitudeAdjustmentMethod(
                latitudeAdjustmentMethod.lower()
            )
        except ValueError:
            raise CalculationMethodError(
                latitudeAdjustmentMethod,
                list(x.value for x in HighLatitudeAdjustmentMethod),
            )

        self._latitude = latitude
        self._longitude = longitude

        try:
            self._date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as err:
            raise ValueError("Invalid date string. Must be 'yyyy-mm-dd'") from err

        if self._calculation_parameters == {}:
            if fajr_angle is not None:
                self._calculation_parameters["fajr"] = fajr_angle
            if maghrib_angle is not None:
                self._calculation_parameters["maghrib"] = maghrib_angle
            if isha_angle is not None:
                self._calculation_parameters["isha"] = isha_angle
        self._calculation_parameters = {
            k.lower(): v for k, v in self._calculation_parameters.items()
        }

        if "shafaq" in self._calculation_parameters:
            self._calculation_parameters["shafaq"] = shafaq

        self._calculation_parameters["midnight"] = {
            MidnightMode.JAFARI: "Jafari",
            MidnightMode.STANDARD: "Standard",
        }[self._midnight_mode]
        self._calculation_parameters["asr"] = {
            School.HANAFI: "Hanafi",
            School.SHAFI: "Standard",
        }[self._school]
        self._calculation_parameters["highLats"] = {
            HighLatitudeAdjustmentMethod.MIDDLE_OF_NIGHT: "NightMiddle",
            HighLatitudeAdjustmentMethod.ONE_SEVENTH: "OneSeventh",
            HighLatitudeAdjustmentMethod.ANGLE_BASED: "AngleBased",
            HighLatitudeAdjustmentMethod.NONE: "None",
        }[self._lat_adj_method]

        if tune is True:
            self._tune = {
                "imsak": imsak_tune,
                "fajr": fajr_tune,
                "sunrise": sunrise_tune,
                "dhuhr": dhuhr_tune,
                "asr": asr_tune,
                "maghrib": maghrib_tune,
                "sunset": sunset_tune,
                "isha": isha_tune,
                "midnight": midnight_tune,
            }
        else:
            self._tune = {}

        # Method-specific tuning
        # https://github.com/islamic-network/api.aladhan.com/blob/bacbfeba9c65e4054ceb45103b1084b55ddbdd2c/api/Utils/PrayerTimesHelper.php#L181
        if calculation_method.lower() == "makkah":
            if self.computeHijriDate()[1] == 9:  # Ramadan
                self._tune.update({"isha": 30})
        elif calculation_method.lower() == "dubai":
            self._tune.update(
                {
                    "dhuhr": 3,
                    "maghrib": 3,
                    "sunset": 3,
                }
            )
        elif calculation_method.lower() == "turkey":
            self._tune.update(
                {
                    "sunrise": -7,
                    "dhuhr": 5,
                    "asr": 4,
                    "maghrib": 7,
                    "sunset": 7,
                }
            )
        elif calculation_method.lower() == "morocco":
            self._tune.update(
                {
                    "dhuhr": 5,
                    "maghrib": 5,
                }
            )
        elif calculation_method.lower() == "portugal":
            self._tune.update(
                {
                    "dhuhr": 5,
                }
            )

        # We always return explicit UTC timestamps, to avoid needing TZ detection
        assert iso8601

    def computeHijriDate(self) -> typing.Tuple[int, int, int]:
        # https://github.com/islamic-network/api.aladhan.com/blob/bacbfeba9c65e4054ceb45103b1084b55ddbdd2c/api/Models/HijriCalendar.php#L118
        intPart: typing.Callable[[float], int] = (
            lambda x: math.ceil(x - 0.0000001)
            if x < -0.0000001
            else math.floor(x + 0.0000001)
        )

        if (
            (self._date.year > 1582)
            or ((self._date.year == 1582) and (self._date.month > 10))
            or (
                (self._date.year == 1582)
                and (self._date.month == 10)
                and (self._date.day > 14)
            )
        ):
            jd = (
                intPart(
                    (
                        1461
                        * (
                            self._date.year
                            + 4800
                            + intPart((self._date.month - 14) / 12)
                        )
                    )
                    / 4
                )
                + intPart(
                    (
                        367
                        * (
                            self._date.month
                            - 2
                            - 12 * (intPart((self._date.month - 14) / 12))
                        )
                    )
                    / 12
                )
                - intPart(
                    (
                        3
                        * (
                            intPart(
                                (
                                    self._date.year
                                    + 4900
                                    + intPart((self._date.month - 14) / 12)
                                )
                                / 100
                            )
                        )
                    )
                    / 4
                )
                + self._date.day
                - 32075
            )
        else:
            jd = (
                367 * self._date.year
                - intPart(
                    (7 * (self._date.year + 5001 + intPart((self._date.month - 9) / 7)))
                    / 4
                )
                + intPart((275 * self._date.month) / 9)
                + self._date.day
                + 1729777
            )

        l = jd - 1948440 + 10632
        n = intPart((l - 1) / 10631)
        l = l - 10631 * n + 354
        j = (intPart((10985 - l) / 5316)) * (intPart((50 * l) / 17719)) + (
            intPart(l / 5670)
        ) * (intPart((43 * l) / 15238))
        l = (
            l
            - (intPart((30 - j) / 15)) * (intPart((17719 * j) / 50))
            - (intPart(j / 16)) * (intPart((15238 * j) / 43))
            + 29
        )
        m = intPart((24 * l) / 709)
        d = l - intPart((709 * m) / 24)
        y = 30 * n + j - 30
        return y, m, d

    def computeDateResponse(self) -> dict[str, typing.Any]:
        hijriDate = self.computeHijriDate()

        holidays = (
            ((1, 10), "Ashura"),
            ((3, 12), "Mawlid al-Nabi"),
            ((7, 27), "Lailat-ul-Miraj"),
            ((8, 15), "Lailat-ul-Bara'at"),
            (
                (
                    9,
                    1,
                ),
                "1st Day of Ramadan",
            ),
            ((9, 21), "Lailat-ul-Qadr"),
            ((9, 23), "Lailat-ul-Qadr"),
            ((9, 25), "Lailat-ul-Qadr"),
            ((9, 27), "Lailat-ul-Qadr"),
            ((9, 29), "Lailat-ul-Qadr"),
            ((10, 1), "Eid-ul-Fitr"),
            ((12, 8), "Hajj"),
            ((12, 9), "Hajj"),
            ((12, 9), "Arafa"),
            ((12, 10), "Eid-ul-Adha"),
            ((12, 10), "Hajj"),
            ((12, 11), "Hajj"),
            ((12, 12), "Hajj"),
            ((12, 13), "Hajj"),
        )

        hijriWeekdays = {
            0: {"en": "Al Athnayn", "ar": "الاثنين"},
            1: {"en": "Al Thalaata", "ar": "الثلاثاء"},
            2: {"en": "Al Arba'a", "ar": "الاربعاء"},
            3: {"en": "Al Khamees", "ar": "الخميس"},
            4: {"en": "Al Juma'a", "ar": "الجمعة"},
            5: {"en": "Al Sabt", "ar": "السبت"},
            6: {"en": "Al Ahad", "ar": "الاحد"},
        }

        hijriMonths = {
            1: {"number": 1, "en": "Muḥarram", "ar": "مُحَرَّم"},
            2: {"number": 2, "en": "Ṣafar", "ar": "صَفَر"},
            3: {"number": 3, "en": "Rabīʿ al-awwal", "ar": "رَبيع الأوّل"},
            4: {"number": 4, "en": "Rabīʿ al-thānī", "ar": "رَبيع الثاني"},
            5: {"number": 5, "en": "Jumādá al-ūlá", "ar": "جُمادى الأولى"},
            6: {"number": 6, "en": "Jumādá al-ākhirah", "ar": "جُمادى الآخرة"},
            7: {"number": 7, "en": "Rajab", "ar": "رَجَب"},
            8: {"number": 8, "en": "Shaʿbān", "ar": "شَعْبان"},
            9: {"number": 9, "en": "Ramaḍān", "ar": "رَمَضان"},
            10: {"number": 10, "en": "Shawwāl", "ar": "شَوّال"},
            11: {"number": 11, "en": "Dhū al-Qaʿdah", "ar": "ذوالقعدة"},
            12: {"number": 12, "en": "Dhū al-Ḥijjah", "ar": "ذوالحجة"},
        }

        return {
            "hijri": {
                "date": "%02d-%02d-%04d" % tuple(reversed(hijriDate)),
                "format": "DD-MM-YYYY",
                "day": "%02d" % hijriDate[2],
                "weekday": hijriWeekdays[self._date.weekday()],
                "month": hijriMonths[hijriDate[1]],
                "year": "%04d" % hijriDate[0],
                "designation": {"abbreviated": "AH", "expanded": "Anno Hegirae"},
                "holidays": [x[1] for x in holidays if x[0] == hijriDate[1:]],
            },
            "gregorian": {
                "date": self._date.strftime("%d-%m-%Y"),
                "format": "DD-MM-YYYY",
                "day": "%02d" % self._date.day,
                "weekday": {"en": self._date.strftime("%A")},
                "month": {"number": self._date.month, "en": self._date.strftime("%B")},
                "year": "%04d" % self._date.year,
                "designation": {"abbreviated": "AD", "expanded": "Anno Domini"},
            },
        }

    def fetch_prayer_times(self) -> dict[str, typing.Any]:
        calculator = PrayTimes()
        calculator.adjust(self._calculation_parameters)
        if len(self._tune):
            calculator.offset.update(self._tune)

        times_float = calculator.getTimes(
            self._date, (self._latitude, self._longitude), timezone=0, format="Float"
        )

        response: dict[str, typing.Any] = {}

        for k, v in times_float.items():
            ts = datetime.combine(self._date, time()) + timedelta(hours=v)
            print(k, v, ts, times_float[k])

            # Rounding
            ts = (ts + timedelta(seconds=30) - timedelta.resolution).replace(
                second=0, microsecond=0
            )
            response[k[0].upper() + k[1:]] = ts.replace(tzinfo=timezone.utc).isoformat()

        response["date"] = self.computeDateResponse()
        return response
