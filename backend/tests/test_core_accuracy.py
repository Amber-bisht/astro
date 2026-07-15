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

if __name__ == '__main__':
    unittest.main()
