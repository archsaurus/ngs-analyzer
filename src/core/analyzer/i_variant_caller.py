from . import *

class IVariantCaller(Protocol):
    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable],
    ): ...
