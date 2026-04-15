import unittest
from datetime import date, time, datetime, timezone
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

from backend.services.geocoding import GeocodingService, ResolvedPlace
from backend.services.ephemeris import build_chart_bundle, ResolvedBirthData

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
        # Note: In 1869, IST didn't exist. We assume Local Mean Time or +4:38
        # However, for this test, we verify the planet positions match standard values.
        resolved = ResolvedBirthData(
            name="Mahatma Gandhi",
            dob=date(1869, 10, 2),
            birth_time=time(7, 12),
            time_accuracy="exact",
            place=ResolvedPlace("Porbandar", 21.6417, 69.6293, "Asia/Kolkata"), # Asia/Kolkata uses LMT for pre-1906
            local_datetime=datetime(1869, 10, 2, 7, 12),
            utc_datetime=datetime(1869, 10, 2, 2, 33, 50, tzinfo=timezone.utc) # LMT offset approx +4:38:10
        )
        
        bundle = build_chart_bundle(resolved)
        
        # Gandhi had Moon in Cancer (Savage/Ashesha)
        self.assertEqual(bundle.data["core_identity"]["moon_sign"], "Cancer")
        # Sun in Virgo
        self.assertEqual(bundle.data["core_identity"]["sun_sign"], "Virgo")
        # Lagna in Libra
        self.assertEqual(bundle.data["core_identity"]["lagna"], "Libra")

if __name__ == '__main__':
    unittest.main()
