from config import Config

DIAMOND_PACKAGES = Config.DIAMOND_PACKAGES

def get_package_info(package_key: str):
    return DIAMOND_PACKAGES.get(package_key)
