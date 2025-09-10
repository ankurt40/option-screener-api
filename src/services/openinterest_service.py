"""
OpenInterest Service

Service for fetching FNO price data from Motilal Oswal API
"""

import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenInterestService:
    """Service for interacting with Motilal Oswal FNO API"""

    def __init__(self):
        self.base_url = "https://cmots.motilaloswal.cloud/fno/api/F/FNO"
        self.headers = {
            'sec-ch-ua-platform': '"macOS"',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpIjoiOTAwIiwibSI6Ikx8U3xJfEN8TnxSfEZ8RHxCfFUiLCJhIjoiMiIsImV4cCI6MTc1NzU1MTI2MywiaXNzIjoiTU9TTCIsImF1ZCI6IkxGIn0.AN3xzcEqV1njmkhbtsDvjUoHY2t2mcvFdFY-wAnQn8Y',
            'Referer': 'https://www.motilaloswal.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'accept': 'text/plain',
            'T': '900'
        }

    async def get_fno_price_data(self, date: str = "30-Sept-2025", instrument_id: str = "2") -> Optional[Dict[str, Any]]:
        """
        Fetch FNO price data from Motilal Oswal API

        Args:
            date: Date in format DD-MMM-YYYY (default: 30-Sept-2025)
            instrument_id: Instrument ID (default: 2)

        Returns:
            Dictionary containing FNO price data or None if error
        """
        try:
            url = f"{self.base_url}/GetPrice"
            params = {
                'Date': date,
                'i': instrument_id
            }

            logger.info(f"🔍 Fetching FNO price data from Motilal Oswal API: {url}")
            logger.debug(f"📊 Request params: {params}")

            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers
                )

                response.raise_for_status()

                # Try to parse as JSON, fallback to text if not JSON
                try:
                    data = response.json()
                    logger.info(f"✅ Successfully fetched FNO price data as JSON")
                    return data
                except Exception:
                    # If not JSON, return as text
                    data = {"raw_response": response.text}
                    logger.info(f"✅ Successfully fetched FNO price data as text")
                    return data

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error fetching FNO price data: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"❌ Request error fetching FNO price data: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching FNO price data: {e}")
            return None

    async def get_fno_data_with_custom_params(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch FNO data with custom parameters

        Args:
            **kwargs: Custom parameters to pass to the API

        Returns:
            Dictionary containing FNO data or None if error
        """
        try:
            url = f"{self.base_url}/GetPrice"

            logger.info(f"🔍 Fetching FNO data with custom params: {kwargs}")

            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(
                    url,
                    params=kwargs,
                    headers=self.headers
                )

                response.raise_for_status()

                try:
                    data = response.json()
                    logger.info(f"✅ Successfully fetched custom FNO data as JSON")
                    return data
                except Exception:
                    data = {"raw_response": response.text}
                    logger.info(f"✅ Successfully fetched custom FNO data as text")
                    return data

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error fetching custom FNO data: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"❌ Request error fetching custom FNO data: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching custom FNO data: {e}")
            return None

    async def extract_series_from_response(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract series data from Motilal Oswal API response, flatten callbackinfo, and convert to nseCode map

        Args:
            data: Raw response from Motilal Oswal API

        Returns:
            Dictionary mapping nseCode to flattened series data or empty dict if not found
        """
        try:
            # Extract only the "data" field from the response
            if isinstance(data, dict) and 'data' in data:
                extracted_data = data['data']
                logger.debug(f"📊 Found 'data' field with keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")

                # Extract the "all" node from extracted_data
                if isinstance(extracted_data, dict) and 'all' in extracted_data:
                    all_data = extracted_data['all']
                    logger.debug(f"📊 Found 'all' field with keys: {list(all_data.keys()) if isinstance(all_data, dict) else 'Not a dict'}")

                    # Extract the "series" from all_data
                    if isinstance(all_data, dict) and 'series' in all_data:
                        series_data = all_data['series']
                        logger.info(f"✅ Successfully extracted 'series' with {len(series_data) if isinstance(series_data, list) else 'unknown'} items")

                        # Flatten callbackinfo and convert to nseCode map
                        if isinstance(series_data, list):
                            series_map = {}
                            for item in series_data:
                                if isinstance(item, dict):
                                    # Flatten the callbackinfo data
                                    flattened_item = self._flatten_callback_info(item)

                                    # Use nseCode as the key
                                    nse_code = flattened_item.get('nseCode')
                                    if nse_code:
                                        series_map[nse_code] = flattened_item
                                    else:
                                        logger.warning(f"⚠️ Item missing nseCode, skipping: {flattened_item}")

                            logger.info(f"✅ Created series map with {len(series_map)} entries indexed by nseCode")
                            return series_map
                        else:
                            return {}
                    else:
                        logger.warning(f"No 'series' field found in all_data. Available keys: {list(all_data.keys()) if isinstance(all_data, dict) else 'Not a dict'}")
                        return {}
                else:
                    logger.warning(f"No 'all' field found in extracted_data. Available keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")
                    return {}
            else:
                logger.warning(f"No 'data' field found in response. Available keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error extracting series from response: {e}")
            return {}

    def _flatten_callback_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten the callbackinfo data from a series item

        Args:
            item: Series item from the API response

        Returns:
            Flattened dictionary with callbackinfo data merged at root level
        """
        try:
            # Start with a copy of the original item
            flattened = item.copy()

            # Check if callbackinfo exists and flatten it
            if 'callbackinfo' in item and isinstance(item['callbackinfo'], dict):
                callback_info = item['callbackinfo']

                # Remove the original callbackinfo field
                flattened.pop('callbackinfo', None)

                # Merge callbackinfo fields into the root level
                for key, value in callback_info.items():
                    # Avoid overwriting existing keys, prefix with 'cb_' if conflict
                    final_key = key if key not in flattened else f"cb_{key}"
                    flattened[final_key] = value

                logger.debug(f"📊 Flattened callbackinfo for item: {item.get('nseCode', 'unknown')}")

            return flattened

        except Exception as e:
            logger.error(f"❌ Error flattening callback info: {e}")
            return item  # Return original item if flattening fails

    async def get_fno_series_with_custom_params(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch FNO data with custom parameters and extract series

        Args:
            **kwargs: Custom parameters to pass to the API

        Returns:
            List of series data or empty list if not found
        """
        try:
            # Get raw data with custom parameters
            data = await self.get_fno_data_with_custom_params(**kwargs)

            if data is None:
                logger.warning("No data received from custom FNO API call")
                return []

            # Extract series from the response
            series_data = await self.extract_series_from_response(data)
            logger.info(f"✅ Successfully processed custom FNO data and extracted {len(series_data)} series items")
            return series_data

        except Exception as e:
            logger.error(f"❌ Error in get_fno_series_with_custom_params: {e}")
            return []

    async def get_fno_series_data(self, date: str = "30-Sept-2025", instrument_id: str = "2") -> Dict[str, Dict[str, Any]]:
        """
        Fetch FNO price data from Motilal Oswal API and extract series

        Args:
            date: Date in format DD-MMM-YYYY (default: 30-Sept-2025)
            instrument_id: Instrument ID (default: 2)

        Returns:
            Dictionary mapping nseCode to flattened series data or empty dict if not found
        """
        try:
            # Create cache key based on date and instrument_id
            cache_key = f"openinterest_fno_data_{date}_{instrument_id}"

            # Check cache first
            from services.cache_service import cache_service
            cached_data = cache_service.get(cache_key)
            if cached_data:
                logger.info(f"📦 Cache hit for OpenInterest FNO data: {cache_key} with {len(cached_data)} entries")
                return cached_data

            logger.info(f"📭 Cache miss for OpenInterest FNO data: {cache_key}, fetching from API")

            # Get raw data
            data = await self.get_fno_price_data(date=date, instrument_id=instrument_id)

            if data is None:
                logger.warning("No data received from FNO API call")
                return {}

            # Extract series from the response
            series_data = await self.extract_series_from_response(data)

            if series_data:
                # Cache the entire map for 1 hour (60 minutes)
                cache_service.set(cache_key, series_data, ttl_minutes=60)
                logger.info(f"💾 Cached OpenInterest FNO data: {cache_key} with {len(series_data)} entries for 1 hour")

            logger.info(f"✅ Successfully processed FNO data and extracted {len(series_data)} series items")
            return series_data

        except Exception as e:
            logger.error(f"❌ Error in get_fno_series_data: {e}")
            return {}

# Global instance
openinterest_service = OpenInterestService()
