from . import *

class IReportDataContainer(abc.ABC):
    @classmethod
    def to_dict(cls, self): return {attr: getattr(self, attr) for attr in vars(self)}

    @classmethod
    def from_list(cls, data_list):
        values = []
        for i in range(len(fields(cls))):
            if i < len(data_list): values.append(data_list[i])
            else: values.append('')
        return cls(*values)

    def __str__(self): return ';\n'.join([f"{key}: {value}" for key, value in vars(self).items()])
