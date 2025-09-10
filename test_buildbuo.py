import asyncio
import sys
import httpx
sys.path.insert(0, 'src')

async def test_buildbuo_api():
    print('🧪 Testing BuildBuo API call...')

    url = 'https://cmots.motilaloswal.cloud/fno/api/F/FNO/GetPrice'
    params = {'Date': '30-Sept-2025', 'i': '2'}
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpIjoiOTAwIiwibSI6Ikx8U3xJfEN8TnxSfEZ8RHxCfFUiLCJhIjoiMiIsImV4cCI6MTc1NzU1MTI2MywiaXNzIjoiTU9TTCIsImF1ZCI6IkxGIn0.AN3xzcEqV1njmkhbtsDvjUoHY2t2mcvFdFY-wAnQn8Y',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'accept': 'text/plain'
    }

    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            print(f'Status Code: {response.status_code}')
            print(f'Response Text (first 200 chars): {response.text[:200]}')

            if response.status_code == 200:
                try:
                    json_data = response.json()
                    print(f'✅ JSON Response Keys: {list(json_data.keys())}')
                    if 'data' in json_data and 'series' in json_data['data']:
                        series = json_data['data']['series']
                        print(f'✅ Found series array with {len(series)} items')
                    return json_data
                except Exception as e:
                    print(f'❌ JSON parsing failed: {e}')
                    return {"raw_response": response.text}
            else:
                print(f'❌ API returned status {response.status_code}')
                return None

    except Exception as e:
        print(f'❌ Request failed: {e}')
        return None

if __name__ == "__main__":
    result = asyncio.run(test_buildbuo_api())
    print(f'Final result: {type(result)}')
