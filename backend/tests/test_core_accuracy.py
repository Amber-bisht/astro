import unittest
from datetime import date, time, datetime, timezone
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

from backend.services.geocoding import GeocodingService, ResolvedPlace
from backend.services.ephemeris import (
    build_chart_bundle,
    ResolvedBirthData,
    is_planet_benefic,
    is_planet_malefic,
    ChartBundle,
)
from backend.services.yogas import _detect_kaal_sarpa
from backend.services.guna_milan import (
    _nadi_cancellation,
    _bhakoot_cancellation,
    nadi_score,
    bhakoot_score,
)
from backend.services.dasha import build_vimshottari_dasha

class TestKundaliReliability(unittest.TestCase):
    def setUp(self):
        self.geo = GeocodingService()

    @patch('backend.services.geocoding.requests.get')
    def test_historical_timezone_google(self, mock_get):
        """Verify that the system passes the correct timestamp to Google Timezone API."""
        # Mock Google Geocoding response
        mock_geocode_resp = MagicMock()
        mock_geocode_resp.status_code = 200
        mock_geocode_resp.json.return_value = {
            "status": "OK",
            "results": [{
                "geometry": {"location": {"lat": 28.6139, "lng": 77.209}},
                "formatted_address": "New Delhi, India"
            }]
        }
        
        # Mock Google Timezone response
        mock_tz_resp = MagicMock()
        mock_tz_resp.status_code = 200
        mock_tz_resp.json.return_value = {
            "status": "OK",
            "timeZoneId": "Asia/Kolkata"
        }
        
        mock_get.side_effect = [mock_geocode_resp, mock_tz_resp]
        
        # We manually set the key to trigger google provider and ensure opencage is off
        with patch.object(self.geo, 'google_key', 'fake-key'), patch.object(self.geo, 'opencage_key', None):
            dob = date(1943, 5, 15)
            birth_time = "12:00"
            
            # This should trigger resolve_birth_details -> _google_timezone with timestamp
            result = self.geo.resolve_birth_details(
                name="War Time Test",
                dob=dob,
                time_value=birth_time,
                time_accuracy="exact",
                place_input="Delhi"
            )
            
            # Verify the second call to requests.get (timezone) had a timestamp around 1943
            tz_call_args = mock_get.call_args_list[1]
            params = tz_call_args[1]['params']
            
            # 1943-05-15 12:00 UTC is approx -840422400
            expected_ts = int(datetime.combine(dob, time(12, 0), tzinfo=timezone.utc).timestamp())
            self.assertEqual(params['timestamp'], expected_ts)
            self.assertEqual(result.place.timezone, "Asia/Kolkata")

    def test_india_war_time_offset(self):
        """Verify that Asia/Kolkata handles the 1942-1945 +6:30 offset correctly."""
        # May 15, 1943 was during War Time (+6:30)
        # We check if ZoneInfo("Asia/Kolkata") gives the correct UTC conversion
        tz = ZoneInfo("Asia/Kolkata")
        dt = datetime(1943, 5, 15, 12, 0, tzinfo=tz)
        
        # UTC should be 12:00 - 6:30 = 05:30
        self.assertEqual(dt.astimezone(timezone.utc).hour, 5)
        self.assertEqual(dt.astimezone(timezone.utc).minute, 30)
        
        # Contrast with standard time (e.g. 1990)
        dt_std = datetime(1990, 5, 15, 12, 0, tzinfo=tz)
        # UTC should be 12:00 - 5:30 = 06:30
        self.assertEqual(dt_std.astimezone(timezone.utc).hour, 6)
        self.assertEqual(dt_std.astimezone(timezone.utc).minute, 30)

    def test_astrology_accuracy_gandhi(self):
        """High-level check of astronomical accuracy for Mahatma Gandhi."""
        # Gandhi: Oct 2, 1869, 07:12 AM, Porbandar (approx 69.6, 21.6)
        # 1869 India must use Pure LMT.
        resolved = ResolvedBirthData(
            name="Mahatma Gandhi",
            dob=date(1869, 10, 2),
            birth_time=time(7, 12),
            time_accuracy="exact",
            place=ResolvedPlace("Porbandar", 21.6417, 69.6293, "Asia/Kolkata"),
            local_datetime=datetime(1869, 10, 2, 7, 12),
            utc_datetime=datetime(1869, 10, 2, 2, 33, 50, tzinfo=timezone.utc),
            is_lmt=True
        )
        
        bundle = build_chart_bundle(resolved)
        self.assertEqual(bundle.data["core_identity"]["moon_sign"], "Cancer")
        self.assertEqual(bundle.data["core_identity"]["lagna"], "Libra")

    def test_mumbai_1940_bombay_time(self):
        """Verify that Mumbai births before 1955 use Bombay Time (+4:51)."""
        # We manually trigger the resolution logic via resolve_birth_details
        with patch.object(self.geo, 'google_key', 'fake-key'), patch.object(self.geo, 'opencage_key', None):
            with patch.object(self.geo, 'autocomplete') as mock_auto:
                mock_auto.return_value = [{
                    "label": "Mumbai, India",
                    "lat": 18.97,
                    "lon": 72.87,
                    "timezone": "Asia/Kolkata"
                }]
                
                res = self.geo.resolve_birth_details(
                    name="Bombay Test",
                    dob=date(1940, 1, 1),
                    time_value="12:00",
                    time_accuracy="exact",
                    place_input="Mumbai"
                )
                
                # Bombay Time is approx +4:51
                # 72.87 * 240 = 17488.8 -> 17489 seconds -> 4h 51m 29s
                offset = res.local_datetime.utcoffset().total_seconds()
                self.assertAlmostEqual(offset, 17491, delta=120) # Approx 4:51
                self.assertTrue(res.is_lmt)
                self.assertEqual(res.local_datetime.tzname(), "Bombay Time")

    def test_india_1890_pure_lmt(self):
        """Verify that any Indian birth before 1906 uses dynamic LMT."""
        with patch.object(self.geo, 'google_key', 'fake-key'), patch.object(self.geo, 'opencage_key', None):
            with patch.object(self.geo, 'autocomplete') as mock_auto:
                # Test with a high-longitude city like Dibrugarh (~94.9E)
                mock_auto.return_value = [{
                    "label": "Dibrugarh, India",
                    "lat": 27.47,
                    "lon": 94.91,
                    "timezone": "Asia/Kolkata"
                }]
                
                res = self.geo.resolve_birth_details(
                    name="LMT Test",
                    dob=date(1890, 1, 1),
                    time_value="12:00",
                    time_accuracy="exact",
                    place_input="Dibrugarh"
                )
                
                # Dibrugarh LMT: 94.91 * 240 = 22778.4s -> 6h 19m 38s
                offset = res.local_datetime.utcoffset().total_seconds()
                self.assertAlmostEqual(offset, 22778, delta=10)
                self.assertTrue(res.is_lmt)
                self.assertEqual(res.local_datetime.tzname(), "LMT")

    def test_kaal_sarpa_yoga_both_directions(self):
        """Verify Kaal Sarpa Yoga detects hemmed planets in both sectors."""
        # 1. Sector 1 (Rahu -> Ketu)
        longitudes_1 = {
            "rahu": 30.0,
            "ketu": 210.0,
            "sun": 45.0,
            "moon": 60.0,
            "mars": 90.0,
            "mercury": 120.0,
            "jupiter": 150.0,
            "venus": 180.0,
            "saturn": 200.0,
        }
        bundle_1 = MagicMock()
        bundle_1.planet_longitudes = longitudes_1
        yogas_1 = _detect_kaal_sarpa(bundle_1)
        self.assertEqual(len(yogas_1), 1)
        self.assertEqual(yogas_1[0]["name"], "Kaal Sarpa Yoga")

        # 2. Sector 2 (Ketu -> Rahu)
        longitudes_2 = {
            "rahu": 30.0,
            "ketu": 210.0,
            "sun": 220.0,
            "moon": 240.0,
            "mars": 270.0,
            "mercury": 300.0,
            "jupiter": 330.0,
            "venus": 0.0,
            "saturn": 15.0,
        }
        bundle_2 = MagicMock()
        bundle_2.planet_longitudes = longitudes_2
        yogas_2 = _detect_kaal_sarpa(bundle_2)
        self.assertEqual(len(yogas_2), 1)
        self.assertEqual(yogas_2[0]["name"], "Kaal Sarpa Yoga")

    def test_nadi_same_rashi_lord_cancellation(self):
        """Verify Nadi dosha is cancelled when rashi lords are the same."""
        boy = MagicMock()
        boy.data = {
            "core_identity": {
                "moon_sign": "Aries",
                "nakshatra": "Ashwini",
                "nakshatra_pada": 1,
            }
        }
        girl = MagicMock()
        girl.data = {
            "core_identity": {
                "moon_sign": "Scorpio",
                "nakshatra": "Ashlesha",
                "nakshatra_pada": 2,
            }
        }
        # Aries and Scorpio are both ruled by Mars
        cancellation = _nadi_cancellation(boy, girl)
        self.assertEqual(cancellation, "Same rashi lord (Mars)")

    def test_bhakoot_friendly_lord_cancellation(self):
        """Verify Bhakoot dosha is cancelled for friendly Moon-Jupiter Rashi lords."""
        boy = MagicMock()
        boy.data = {
            "core_identity": {
                "moon_sign": "Cancer"
            }
        }
        girl = MagicMock()
        girl.data = {
            "core_identity": {
                "moon_sign": "Sagittarius"
            }
        }
        cancellation = _bhakoot_cancellation(boy, girl)
        self.assertIsNotNone(cancellation)
        self.assertIn("friendly or neutral", cancellation)

    def test_vimshottari_dasha_custom_year_length(self):
        """Verify Vimshottari Dasha calculations honor custom year lengths."""
        # Moon at 0.0 (beginning of Ketu)
        dasha_365 = build_vimshottari_dasha(0.0, datetime(2000, 1, 1, tzinfo=timezone.utc), year_length=365.0)
        dasha_360 = build_vimshottari_dasha(0.0, datetime(2000, 1, 1, tzinfo=timezone.utc), year_length=360.0)
        
        # Ketu is 7 years.
        # Duration for 365-day year: 7 * 365 = 2555 days
        # Duration for 360-day year: 7 * 360 = 2520 days
        diff_365 = (dasha_365.major_periods[0].end - dasha_365.major_periods[0].start).days
        diff_360 = (dasha_360.major_periods[0].end - dasha_360.major_periods[0].start).days
        self.assertEqual(diff_365, 2555)
        self.assertEqual(diff_360, 2520)

    def test_dynamic_planet_benefic_malefic(self):
        """Verify dynamic Moon and Mercury benefic/malefic classifications."""
        # 1. Moon bright (180 deg elongation from Sun)
        longitudes_bright = {"sun": 0.0, "moon": 180.0}
        self.assertTrue(is_planet_benefic("Moon", longitudes_bright))
        self.assertFalse(is_planet_malefic("Moon", longitudes_bright))

        # 2. Moon dark (10 deg elongation from Sun)
        longitudes_dark = {"sun": 0.0, "moon": 10.0}
        self.assertFalse(is_planet_benefic("Moon", longitudes_dark))
        self.assertTrue(is_planet_malefic("Moon", longitudes_dark))

        # 3. Mercury alone (benefic)
        longitudes_mercury_alone = {"mercury": 45.0, "sun": 120.0}
        self.assertTrue(is_planet_benefic("Mercury", longitudes_mercury_alone))

        # 4. Mercury conjunct Saturn (malefic)
        longitudes_mercury_saturn = {"mercury": 45.0, "saturn": 50.0}  # Same sign (Taurus)
        self.assertFalse(is_planet_benefic("Mercury", longitudes_mercury_saturn))
        self.assertTrue(is_planet_malefic("Mercury", longitudes_mercury_saturn))

    def test_combustion_check(self):
        """Verify that planetary combustion logic works correctly."""
        # Gandhi birth data as reference for bundle creation
        resolved = ResolvedBirthData(
            name="Porbandar LMT",
            dob=date(1869, 10, 2),
            birth_time=time(7, 12),
            time_accuracy="exact",
            place=ResolvedPlace("Porbandar", 21.6417, 69.6293, "Asia/Kolkata"),
            local_datetime=datetime(1869, 10, 2, 7, 12),
            utc_datetime=datetime(1869, 10, 2, 2, 33, 50, tzinfo=timezone.utc),
            is_lmt=True
        )
        bundle = build_chart_bundle(resolved)
        # Verify that Sun and Rahu/Ketu are not marked combust
        self.assertFalse(bundle.data["planets"]["sun"]["is_combust"])
        self.assertFalse(bundle.data["planets"]["rahu"]["is_combust"])
        self.assertFalse(bundle.data["planets"]["ketu"]["is_combust"])

    def test_neechabhanga_moon_kendra(self):
        """Verify that Neechabhanga is detected if the debilitated planet is in a Kendra from the Moon."""
        from backend.services.yogas import _detect_neechabhanga
        
        bundle = MagicMock()
        bundle.planet_houses = {
            "sun": 2,       # Sun in H2 (not Kendra from Lagna)
            "moon": 11,     # Moon in H11 from Lagna
            "mars": 1,
            "mercury": 1,
            "jupiter": 1,
            "venus": 1,
            "saturn": 1,
            "rahu": 1,
            "ketu": 1
        }
        bundle.data = {
            "planet_strength": {"sun": "debilitated"},
            "planets": {
                "sun": {"sign": "Libra"}
            }
        }
        
        # Sun (H2) is in a Kendra from the Moon (H11) since ((2 - 11) % 12) + 1 = 4.
        yogas = _detect_neechabhanga(bundle)
        self.assertEqual(len(yogas), 1)
        self.assertEqual(yogas[0]["name"], "Neechabhanga Raj Yoga")
        self.assertIn("Kendra from Moon", yogas[0]["description"])

    def test_independent_viparita_yogas(self):
        """Verify that Harsha, Sarala, and Vimala Yogas are detected independently."""
        from backend.services.yogas import _detect_viparita_raj
        
        bundle = MagicMock()
        # 6th lord in 8th house (dusthana)
        bundle.data = {
            "lords_mapping": {
                "6": "Mars",
                "8": "Mercury",
                "12": "Saturn"
            }
        }
        bundle.planet_houses = {
            "mars": 8,       # 6th lord Mars in 8th house
            "mercury": 1,    # 8th lord in 1st house (not dusthana)
            "saturn": 1      # 12th lord in 1st house
        }
        
        yogas = _detect_viparita_raj(bundle)
        self.assertEqual(len(yogas), 1)
        self.assertEqual(yogas[0]["name"], "Harsha Viparita Raj Yoga")

    def test_raj_yoga_mutual_aspect_and_exchange(self):
        """Verify sign exchange (Parivartana) and mutual aspects form Kendra-Trikona Raj Yogas."""
        from backend.services.yogas import _detect_raj_yogas
        
        bundle = MagicMock()
        # H1 (Kendra) lord Mars in Scorpio (own sign, but let's test exchange)
        # H5 (Trikona) lord Sun
        bundle.data = {
            "lords_mapping": {
                "1": "Mars",
                "4": "Venus",
                "7": "Venus",
                "10": "Saturn",
                "5": "Sun",
                "9": "Jupiter"
            },
            "planets": {
                "mars": {"sign": "Leo"},  # Mars (H1 lord) in Leo (Sun's sign)
                "sun": {"sign": "Aries"}   # Sun (H5 lord) in Aries (Mars's sign)
            },
            "aspects": {
                "aspects_given": {
                    "mars": [],
                    "sun": []
                }
            }
        }
        bundle.planet_houses = {
            "mars": 5,
            "sun": 1,
            "venus": 1,
            "saturn": 1,
            "jupiter": 1,
            "rahu": 1,
            "ketu": 1
        }
        
        yogas = _detect_raj_yogas(bundle)
        names = [y["name"] for y in yogas]
        self.assertIn("Raj Yoga (Sign Exchange)", names)

    def test_multi_chart_manglik(self):
        """Verify Manglik Dosha checks relative to Lagna, Moon, and Venus."""
        from backend.services.chart_builder import compute_manglik
        
        bundle = MagicMock()
        bundle.planet_houses = {
            "mars": 5,      # Mars in H5 from Lagna (Not Manglik from Lagna)
            "moon": 11,     # Moon in H11 from Lagna -> Mars is in H7 from Moon ((5 - 11) % 12 + 1 = 7)
            "venus": 1,
            "jupiter": 1
        }
        bundle.planet_sign_indices = {
            "mars": 4,      # Leo
            "moon": 10,     # Aquarius
            "venus": 0      # Aries
        }
        bundle.data = {
            "planet_strength": {"mars": "neutral"},
            "aspects": {
                "aspects_given": {
                    "jupiter": []
                }
            }
        }
        
        res = compute_manglik(bundle, partner=None)
        self.assertTrue(res["present"])
        self.assertTrue(res["moon_manglik"])
        self.assertFalse(res["lagna_manglik"])
        self.assertEqual(res["severity"], "high") # Mars is in 7th from Moon

    def test_complex_chart_integration_gandhi(self):
        """Perform a complex integration test using Mahatma Gandhi's birth data."""
        # Gandhi: Oct 2, 1869, 07:12 AM, Porbandar (69.6293E, 21.6417N)
        resolved = ResolvedBirthData(
            name="Mahatma Gandhi",
            dob=date(1869, 10, 2),
            birth_time=time(7, 12),
            time_accuracy="exact",
            place=ResolvedPlace("Porbandar", 21.6417, 69.6293, "Asia/Kolkata"),
            local_datetime=datetime(1869, 10, 2, 7, 12),
            utc_datetime=datetime(1869, 10, 2, 2, 33, 50, tzinfo=timezone.utc),
            is_lmt=True
        )
        
        from backend.services.chart_builder import build_single_chart
        chart = build_single_chart(resolved)
        
        # 1. Assert basic placements
        self.assertEqual(chart["core_identity"]["lagna"], "Libra")
        self.assertEqual(chart["core_identity"]["moon_sign"], "Cancer")
        
        # 2. Check Bhava Chalit shifts:
        for p_key, payload in chart["planets"].items():
            self.assertIn("bhava_house", payload)
            self.assertIn("is_combust", payload)
            
        # 3. Yogas check:
        yoga_names = [y["name"] for y in chart["yogas"]]
        # Gandhi has Gajakesari Yoga (Jupiter in Aries H7, Moon in Cancer H10)
        self.assertIn("Gajakesari Yoga", yoga_names)
        
        # 4. Combustion check for Gandhi:
        self.assertIn("is_combust", chart["planets"]["mercury"])
        
        # 5. Manglik Dosha:
        self.assertTrue(chart["doshas"]["manglik"]["present"])
        self.assertTrue(chart["doshas"]["manglik"]["lagna_manglik"])
        self.assertTrue(chart["doshas"]["manglik"]["cancellation"]) # Aspect of Jupiter cancels it!
        self.assertEqual(chart["doshas"]["manglik"]["severity"], "low") # low because it is cancelled!

    def test_modern_ist_modi(self):
        """Verify calculations for a modern Indian birth after timezone standardization."""
        # Narendra Modi: Sept 17, 1950, 11:00 AM, Vadnagar, Gujarat, India (~72.64, 23.78)
        resolved = ResolvedBirthData(
            name="Narendra Modi",
            dob=date(1950, 9, 17),
            birth_time=time(11, 0),
            time_accuracy="exact",
            place=ResolvedPlace("Vadnagar", 23.7844, 72.6375, "Asia/Kolkata"),
            local_datetime=datetime(1950, 9, 17, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
            utc_datetime=datetime(1950, 9, 17, 5, 30, tzinfo=timezone.utc),
            is_lmt=False
        )
        bundle = build_chart_bundle(resolved)
        # Verify basic placements:
        # Modi is Scorpio Lagna, Scorpio Moon (Vrischika) under Lahiri
        self.assertEqual(bundle.data["core_identity"]["moon_sign"], "Scorpio")
        self.assertEqual(bundle.data["core_identity"]["lagna"], "Scorpio")
        self.assertFalse(bundle.resolved_birth.is_lmt)

    def test_foreign_obama(self):
        """Verify calculations for a foreign birth (Honolulu, Hawaii, USA)."""
        # Barack Obama: Aug 4, 1961, 7:24 PM (19:24), Honolulu, Hawaii, USA (~ -157.86, 21.31)
        resolved = ResolvedBirthData(
            name="Barack Obama",
            dob=date(1961, 8, 4),
            birth_time=time(19, 24),
            time_accuracy="exact",
            place=ResolvedPlace("Honolulu", 21.3069, -157.8583, "Pacific/Honolulu"),
            local_datetime=datetime(1961, 8, 4, 19, 24, tzinfo=ZoneInfo("Pacific/Honolulu")),
            utc_datetime=datetime(1961, 8, 5, 5, 24, tzinfo=timezone.utc),
            is_lmt=False
        )
        bundle = build_chart_bundle(resolved)
        # Vedic Placements: Capricorn Lagna (Makar) and Taurus Moon (Vrishabha)
        self.assertEqual(bundle.data["core_identity"]["lagna"], "Capricorn")
        self.assertEqual(bundle.data["core_identity"]["moon_sign"], "Taurus")
        self.assertFalse(bundle.resolved_birth.is_lmt)

if __name__ == '__main__':
    unittest.main()
