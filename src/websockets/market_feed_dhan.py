import logging
import os
import asyncio
import websockets
import json
import ssl
import struct
from dhanhq import DhanContext, MarketFeed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU3MzI2MTU3LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwODA2NjUzMCJ9.YnPPDghUzQ7QORhK6DSflk12hNyJzydD59KnNHA6nFPmH8-3Tk20HkXXUTidMyvwdahOPoqL6XgnTMp2-ooQ0g"
client_id = "1108066530"

# Disable SSL verification for development (to fix certificate issues)
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

# WebSocket URL for Dhan depth API
ws_url = f"wss://depth-api-feed.dhan.co/twentydepth?token={access_token}&clientId={client_id}&authType=2"

# JSON request payload
depth_request = {
    "RequestCode": 23,
    "InstrumentCount": 2,
    "InstrumentList": [
        {
            "ExchangeSegment": "NSE_EQ",
            "SecurityId": "1333"
        },
        {
            "ExchangeSegment": "NSE_FNO",
            "SecurityId": "532540"
        }
    ]
}

def parse_binary_market_depth(data):
    """Parse binary market depth data from Dhan API according to official documentation"""
    try:
        if len(data) < 8:
            return {"error": "Message too short for header", "raw_length": len(data)}

        # Parse Response Header (8 bytes)
        feed_response_code = data[0]
        message_length = struct.unpack('<H', data[1:3])[0]  # int16 little-endian
        exchange_segment = data[3]
        security_id = struct.unpack('<I', data[4:8])[0]  # int32 little-endian

        parsed_data = {
            "header": {
                "feed_response_code": feed_response_code,
                "message_length": message_length,
                "exchange_segment": exchange_segment,
                "security_id": security_id
            }
        }

        logger.info(f"📊 Feed Response Code: {feed_response_code}")
        logger.info(f"🔢 Security ID: {security_id}")
        logger.info(f"📏 Message Length: {message_length}")
        logger.info(f"🏢 Exchange Segment: {exchange_segment}")

        # Parse payload based on feed response code
        if feed_response_code == 2:  # Ticker Packet
            if len(data) >= 16:
                ltp = struct.unpack('<f', data[8:12])[0]  # float32
                ltt = struct.unpack('<I', data[12:16])[0]  # int32
                parsed_data["ticker"] = {
                    "last_traded_price": ltp,
                    "last_trade_time": ltt
                }
                logger.info(f"💰 LTP: {ltp}, LTT: {ltt}")

        elif feed_response_code == 4:  # Quote Packet
            if len(data) >= 50:
                ltp = struct.unpack('<f', data[8:12])[0]
                ltq = struct.unpack('<H', data[12:14])[0]  # int16
                ltt = struct.unpack('<I', data[14:18])[0]
                atp = struct.unpack('<f', data[18:22])[0]
                volume = struct.unpack('<I', data[22:26])[0]
                total_sell_qty = struct.unpack('<I', data[26:30])[0]
                total_buy_qty = struct.unpack('<I', data[30:34])[0]
                day_open = struct.unpack('<f', data[34:38])[0]
                day_close = struct.unpack('<f', data[38:42])[0]
                day_high = struct.unpack('<f', data[42:46])[0]
                day_low = struct.unpack('<f', data[46:50])[0]

                parsed_data["quote"] = {
                    "last_traded_price": ltp,
                    "last_traded_quantity": ltq,
                    "last_trade_time": ltt,
                    "average_trade_price": atp,
                    "volume": volume,
                    "total_sell_quantity": total_sell_qty,
                    "total_buy_quantity": total_buy_qty,
                    "day_open": day_open,
                    "day_close": day_close,
                    "day_high": day_high,
                    "day_low": day_low
                }
                logger.info(f"💰 Quote - LTP: {ltp}, Volume: {volume}, High: {day_high}, Low: {day_low}")

        elif feed_response_code == 5:  # OI Data
            if len(data) >= 12:
                open_interest = struct.unpack('<I', data[8:12])[0]
                parsed_data["oi"] = {
                    "open_interest": open_interest
                }
                logger.info(f"📈 Open Interest: {open_interest}")

        elif feed_response_code == 6:  # Prev Close
            if len(data) >= 16:
                prev_close = struct.unpack('<f', data[8:12])[0]
                prev_oi = struct.unpack('<I', data[12:16])[0]
                parsed_data["prev_close"] = {
                    "previous_close_price": prev_close,
                    "previous_open_interest": prev_oi
                }
                logger.info(f"📊 Prev Close: {prev_close}, Prev OI: {prev_oi}")

        elif feed_response_code == 8:  # Full Packet
            if len(data) >= 162:
                # Parse main data (same as quote packet first)
                ltp = struct.unpack('<f', data[8:12])[0]
                ltq = struct.unpack('<H', data[12:14])[0]
                ltt = struct.unpack('<I', data[14:18])[0]
                atp = struct.unpack('<f', data[18:22])[0]
                volume = struct.unpack('<I', data[22:26])[0]
                total_sell_qty = struct.unpack('<I', data[26:30])[0]
                total_buy_qty = struct.unpack('<I', data[30:34])[0]
                open_interest = struct.unpack('<I', data[34:38])[0]
                highest_oi = struct.unpack('<I', data[38:42])[0]
                lowest_oi = struct.unpack('<I', data[42:46])[0]
                day_open = struct.unpack('<f', data[46:50])[0]
                day_close = struct.unpack('<f', data[50:54])[0]
                day_high = struct.unpack('<f', data[54:58])[0]
                day_low = struct.unpack('<f', data[58:62])[0]

                # Parse Market Depth (5 packets of 20 bytes each, starting at byte 62)
                market_depth = []
                for i in range(5):
                    start_idx = 62 + (i * 20)
                    if start_idx + 20 <= len(data):
                        bid_qty = struct.unpack('<I', data[start_idx:start_idx+4])[0]
                        ask_qty = struct.unpack('<I', data[start_idx+4:start_idx+8])[0]
                        bid_orders = struct.unpack('<H', data[start_idx+8:start_idx+10])[0]
                        ask_orders = struct.unpack('<H', data[start_idx+10:start_idx+12])[0]
                        bid_price = struct.unpack('<f', data[start_idx+12:start_idx+16])[0]
                        ask_price = struct.unpack('<f', data[start_idx+16:start_idx+20])[0]

                        depth_level = {
                            "level": i + 1,
                            "bid_quantity": bid_qty,
                            "ask_quantity": ask_qty,
                            "bid_orders": bid_orders,
                            "ask_orders": ask_orders,
                            "bid_price": bid_price,
                            "ask_price": ask_price
                        }
                        market_depth.append(depth_level)

                parsed_data["full"] = {
                    "last_traded_price": ltp,
                    "last_traded_quantity": ltq,
                    "last_trade_time": ltt,
                    "average_trade_price": atp,
                    "volume": volume,
                    "total_sell_quantity": total_sell_qty,
                    "total_buy_quantity": total_buy_qty,
                    "open_interest": open_interest,
                    "highest_oi": highest_oi,
                    "lowest_oi": lowest_oi,
                    "day_open": day_open,
                    "day_close": day_close,
                    "day_high": day_high,
                    "day_low": day_low,
                    "market_depth": market_depth
                }

                logger.info(f"📊 Full Data - LTP: {ltp}, Volume: {volume}, OI: {open_interest}")
                logger.info(f"📈 Market Depth Levels: {len(market_depth)}")
                for level in market_depth[:3]:  # Show first 3 levels
                    logger.info(f"  Level {level['level']}: Bid {level['bid_price']}({level['bid_quantity']}) | Ask {level['ask_price']}({level['ask_quantity']})")

        else:
            logger.warning(f"⚠️ Unknown feed response code: {feed_response_code}")
            parsed_data["unknown"] = {
                "raw_payload_hex": data[8:].hex() if len(data) > 8 else ""
            }

        return parsed_data

    except Exception as e:
        logger.error(f"❌ Error parsing binary data: {e}")
        return {
            "error": str(e),
            "raw_length": len(data),
            "raw_hex": data[:50].hex() if len(data) > 0 else ""
        }

async def dhan_depth_websocket():
    """Connect to Dhan depth API WebSocket and stream market depth data"""

    # Create SSL context that ignores certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        logger.info("🚀 Connecting to Dhan Depth API WebSocket...")
        logger.info(f"📡 URL: {ws_url}")

        async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
            logger.info("✅ WebSocket connection established successfully!")

            # Send the depth request
            request_json = json.dumps(depth_request)
            logger.info(f"📤 Sending request: {request_json}")
            await websocket.send(request_json)
            logger.info("✅ Request sent successfully!")

            # Listen for responses
            logger.info("👂 Listening for responses...")
            message_count = 0

            async for message in websocket:
                try:
                    message_count += 1
                    logger.info(f"📥 Message #{message_count} received")

                    # Check if message is text or binary
                    if isinstance(message, str):
                        # Text message - try to parse as JSON
                        try:
                            response_data = json.loads(message)
                            logger.info(f"📄 JSON response: {json.dumps(response_data, indent=2)}")
                        except json.JSONDecodeError:
                            logger.info(f"📄 Text message: {message}")
                    else:
                        # Binary message - parse as market depth data
                        logger.info(f"📊 Binary message received ({len(message)} bytes)")
                        parsed_data = parse_binary_market_depth(message)
                        logger.info(f"🔍 Parsed data: {json.dumps(parsed_data, indent=2)}")

                    # Log specific fields if available
                    if message_count >= 10:
                        logger.info("🔄 Received 10 messages, continuing to monitor...")
                        # Reset counter to avoid too much logging
                        message_count = 0

                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    logger.error(f"📊 Message type: {type(message)}")
                    if isinstance(message, bytes):
                        logger.error(f"📊 Binary message length: {len(message)}")
                    else:
                        logger.error(f"📊 Raw message: {message}")

    except websockets.exceptions.ConnectionClosed:
        logger.warning("🔌 WebSocket connection closed")
    except websockets.exceptions.InvalidURI:
        logger.error("❌ Invalid WebSocket URI")
    except websockets.exceptions.InvalidHandshake:
        logger.error("❌ WebSocket handshake failed")
    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {e}")

def main_original_dhan_feed():
    """Original Dhan market feed implementation"""
    try:
        logger.info("🚀 Starting Original Dhan Market Feed WebSocket connection...")

        # ...existing code...
        dhan_context = DhanContext(client_id, access_token)

        # Structure for subscribing is (exchange_segment, "security_id", subscription_type)
        instruments = [(MarketFeed.NSE, "1333", MarketFeed.Ticker),   # Ticker - Ticker Data
                       (MarketFeed.NSE, "1333", MarketFeed.Quote),     # Quote - Quote Data
                       (MarketFeed.NSE, "1333", MarketFeed.Full),      # Full - Full Packet
                       (MarketFeed.NSE, "11915", MarketFeed.Ticker),
                       (MarketFeed.NSE, "11915", MarketFeed.Full)]

        version = "v2"

        # Create market feed without ssl_context parameter
        data = MarketFeed(dhan_context, instruments, version)

        logger.info("✅ MarketFeed initialized successfully")
        logger.info(f"📡 Subscribed to {len(instruments)} instruments")

        # Run the market feed
        while True:
            try:
                data.run_forever()
                response = data.get_data()
                if response:
                    logger.info(f"📊 Market Data: {response}")
                else:
                    logger.debug("No data received")

            except KeyboardInterrupt:
                logger.info("🛑 Stopping market feed...")
                break
            except Exception as e:
                logger.error(f"❌ Error in market feed loop: {e}")
                # Wait a bit before retrying
                asyncio.sleep(5)

    except Exception as e:
        logger.error(f"❌ Failed to initialize market feed: {e}")
        logger.error("💡 Try updating certificates or check network connection")

async def main():
    """Main function to run the depth API WebSocket"""
    logger.info("🎯 Starting Dhan Depth API WebSocket Client")
    logger.info(f"🔑 Client ID: {client_id}")
    logger.info(f"📋 Instruments: NSE_EQ:1333, NSE_FNO:532540")

    try:
        await dhan_depth_websocket()
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    # Run the async WebSocket client
    asyncio.run(main())
