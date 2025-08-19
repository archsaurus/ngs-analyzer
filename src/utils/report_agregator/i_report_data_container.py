"""
    Defines the IReportDataContainer interface, which provides methods for
    serializing and deserializing data container instances, along with a
    string representation method.
"""

from abc import ABC
from dataclasses import fields

class IReportDataContainer(ABC):
    """
        Interface for report data containers, providing utility methods
        for converting to dictionary, creating instances from lists,
        and generating string representations.
    """
    @classmethod
    def to_dict(cls, self):
        """
            Convert the dataclass instance to a dictionary.

            Args:
                self:
                    The instance of the data container.

            Returns:
                dict:
                    A dictionary with attribute names
                    as keys and attribute values.
        """
        return {attr: getattr(self, attr) for attr in vars(self)}

    @classmethod
    def from_list(cls, data_list):
        """
            Create an instance of the class from a list of values.

            Args:
                data_list (list):
                    List of values corresponding to the class fields.

            Returns:
                An instance of the class initialized with the provided values.
        """
        values = []
        for i in range(len(fields(cls))):
            if i < len(data_list):
                values.append(data_list[i])
            else: values.append('')
        return cls(*values)

    def __str__(self):
        return ';\n'.join([
            f"{key}: {value}" for key, value in vars(self).items()])
