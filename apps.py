from configuration.utils.app_config_class import get_app_config_class

Config = get_app_config_class(__file__)


def ready(self):
    import categories.signals


Config.ready = ready
