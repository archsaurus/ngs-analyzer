"""
    A module for representing and managing sample sheet data.

    This module defines data structures for organizing
    sample sheet information, allowing for flexible storage
    of various data types within different sections.
    It is designed to handle both simple key-value pairs
    and more complex structures within each section
    of the sample sheet.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Union

@dataclass
class Section:
    """
        Represents a section within the sample sheet.

        Attributes:
            name (str):
                The name of the section.
            data (Union[Dict[str, str], List[Union[Dict, str]]]):
                The data associated with the section,
                which can be a dictionary of string key-value pairs
                or a list containing dictionaries or strings.
    """
    name: str
    data: Union[dict[str, str], list[Union[dict, str]]]

@dataclass
class SampleSheetContainer:
    """
        Container for managing multiple sections of a sample sheet.

        Attributes:
            sections (List[Section]):
                A list of Section objects.
    """
    sections: list[Section] = field(default_factory=list)

    def add_section(self, section: Section) -> None:
        """
            Adds a new section to the container.

            Args:
                section (Section):
                    The Section object to add.
        """
        self.sections.append(section)

    def get_sections(self) -> list[Section]:
        """
            Retrieves all sections stored in the container.

            Returns:
                list[Section]: The list of Section objects.
        """
        return self.sections
