import json
import asyncio
from websockets.server import serve
from assistant import conversation_handler, logger
from assistant.data_manager import load_settings, save_settings


SERVER_PORT = 6969
client = None

async def _handle_connection(websocket, path):
    async for message in websocket:
        command = message[:4]
        logger.info(f'Reciving message of type: {command}')

        try:
            if command == '-hi-':
                response = conversation_handler.get_last_message()
                await websocket.send(response)
            elif command == 'text':
                response = conversation_handler.ask_yumi(message[5:])
                await websocket.send(response)

            elif command == 'load':
                settings = load_settings(message[5:])
                await websocket.send(json.dumps(settings))
            elif command == 'save':
                data_to_save = json.loads(message[5:])
                key = data_to_save['key']
                settings = data_to_save['settings']
                save_settings(key, settings)
                continue
        except Exception as e:
            logger.error(f'[YUMIAI] Erro while handling {command}: {str(e)}')

async def _run():
    async with serve(_handle_connection, '127.0.0.1', SERVER_PORT, ping_interval=None):
        await asyncio.Future()

try:
    logger.info(f'Starting streaming server at ws://127.0.0.1:{SERVER_PORT}')
    asyncio.run(_run())
except KeyboardInterrupt:
    pass
except Exception as e:
    logger.error(str(e))

# plugins = plugin_manager.PluginManager()
# plugins.initialize_plugins()

# response, tokens_count = gpt_caller.ask("Yumi do you love me?")
# plugins.process(response)