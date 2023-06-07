import os
from typing import Dict
from assistant.data_manager import load_plugin_settings
from assistant import logger


def execute(args: list[str]):
    program = args[1].replace('\_', '_').strip()

    avaliable_programs: Dict[str, str] = load_plugin_settings('programs')
    if program not in avaliable_programs:
        raise ValueError(f"Not a valid program ({program})")

    path = avaliable_programs[program].replace('\'', "\"")
    os.system(f'{path}')
    logger.info(f"Running program: {program}")