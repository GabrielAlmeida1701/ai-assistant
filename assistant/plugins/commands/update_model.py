from assistant import logger


def execute(args: list[str]):
    model_name = args[1]
    logger.info(f"Updating model: {model_name}")