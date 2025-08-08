from . import *

class VariantCallerFactory(LoggerMixin):
    def __init__(self, logger: Optional[logging.Logger]=None):
        super().__init__(logger=logger)

    @staticmethod
    def create_caller(
        caller_config: dict[str, str],
        configurator: Configurator
    ) -> IVariantCaller:
        match caller_config['name']:
            case 'pisces':
                return PiscesVariantCaller(
                    configurator=configurator,
                    logger=configurator.logger)

            case 'unifiedgenotyper':
                return UnifiedGenotyperVariantCaller(
                    configurator=configurator,
                    logger=configurator.logger)

            case 'freebayes':
                return FreebayesVariantCaller(
                    configurator=configurator,
                    logger=configurator.logger)

            case _:
                self.logger.critical(
                    f"Unknown caller type '{caller_config['name']}'")
                raise ConfigurationError()
