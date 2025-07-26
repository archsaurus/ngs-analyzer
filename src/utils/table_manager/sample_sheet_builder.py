from src.core.base import *

from .sample_sheet_container import SampleSheetContainer

class SampleSheetBuilder:
    """
        A builder class for constructing a sample sheet text from a container of sections.

        Attributes:
            container (SampleSheetContainer): The container holding the sections to be included in the sample sheet.
            lines (list): A list of strings representing each line of the constructed sample sheet.
            separator (str): The separator used to join values in the output (default is comma).
    """

    def __init__(self, container: SampleSheetContainer, separator: str=','):
        """
            Initializes the SampleSheetBuilder with a container and optional separator.

            Args:
                container (SampleSheetContainer): The container with sections to build from.
                separator (str, optional): The separator string used in the output. Defaults to ','.

            Raises:
                TypeError: If the provided container is not an instance of SampleSheetContainer.
        """
        if not isinstance(container, SampleSheetContainer): raise TypeError
        
        self.container = container
        self.lines = []

        if len(separator) == 1 and len(re.findall(r"\w", separator)) == 0: self.separator = separator
        else: self.separator = ','

    def build(self) -> None:
        """
            Builds the sample sheet lines from the sections in the container.
            Populates the self.lines list with the constructed lines.
        """
        for section in self.container.get_sections():
            self.lines.append(f"[{section.name}]")
            section_data = section.data

            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, list):
                        line_str = f"{self.separator}".join(value)
                        self.lines.append(str(key) + f"{self.separator}" + line_str)
                    else: self.lines.append(str(key) + f"{self.separator}" + str(value))
            elif isinstance(section_data, list): self.lines.extend(section_data)
            else: self.lines.append(str(section_data))
            self.lines.append('')

    def get_lines(self) -> list[str]:
        """
            Retrieves the constructed sample sheet lines.

            Returns:
                list: A list of strings representing the sample sheet.
        """
        return self.lines

    def save_to_csv(self, path: PathLike[AnyStr]) -> None:
        """
            Saves the constructed sample sheet to a CSV file at the specified path.

            Args:
                path (PathLike[AnyStr]): The file path where the sample sheet will be saved.

            Raises:
                Exception: Propagates any exception raised during file operations.
        """
        try:
            with open(path, 'w') as fd:
                for line in self.lines: print(line, file=fd)
        except Exception as e: raise e
