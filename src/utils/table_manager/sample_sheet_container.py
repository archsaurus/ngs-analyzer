from src.core.base import *
from . import *

from dataclasses import dataclass, field
from typing import Dict, List, Union

@dataclass
class Section:
    """
        Represents a section within the sample sheet.

        Attributes:
            name (str): \
                The name of the section.
            data (Union[Dict[str, str], List[Union[Dict, str]]]): \
                The data associated with the section, \
            which can be a dictionary of string key-value pairs \
                or a list containing dictionaries or strings.
    """
    name: str
    data: Union[Dict[str, str], List[Union[Dict, str]]]

@dataclass
class SampleSheetContainer:
    """
        Container for managing multiple sections of a sample sheet.

        Attributes:
            sections (List[Section]): A list of Section objects.
    """
    sections: List[Section] = field(default_factory=list)

    def add_section(self, section: Section) -> None:
        """
            Adds a new section to the container.

            Args:
                section (Section): The Section object to add.
        """
        self.sections.append(section)

    def get_sections(self) -> List[Section]:
        """
            Retrieves all sections stored in the container.

            Returns:
                List[Section]: The list of Section objects.
        """
        return self.sections
