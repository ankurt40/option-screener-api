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

    async def extract_series_from_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract series data from Motilal Oswal API response

        Args:
            data: Raw response from Motilal Oswal API

        Returns:
            List of series data or empty list if not found
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
                        return series_data if isinstance(series_data, list) else []
                    else:
                        logger.warning(f"No 'series' field found in all_data. Available keys: {list(all_data.keys()) if isinstance(all_data, dict) else 'Not a dict'}")
                        return []
                else:
                    logger.warning(f"No 'all' field found in extracted_data. Available keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")
                    return []
            else:
                logger.warning(f"No 'data' field found in response. Available keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return []

        except Exception as e:
            logger.error(f"❌ Error extracting series from response: {e}")
            return []

# Global instance
openinterest_service = OpenInterestService()
