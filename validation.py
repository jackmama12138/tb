from logger import logger


def validate_params(params, required_fields):
    missing_fields = [field for field in required_fields if field not in params]
    if missing_fields:
        error_msg = f"缺少参数: {', '.join(missing_fields)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
