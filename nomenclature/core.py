from pathlib import Path
import pandas as pd
import yaml

from pyam import IamDataFrame
from pyam.utils import write_sheet

from nomenclature.codes import CodeList
from nomenclature.validation import validate


class DataStructureDefinition:
    """Definition of datastructure codelists for dimensions used in the IAMC format"""

    def __init__(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        if not path.is_dir():
            raise NotADirectoryError(f"Definitions directory not found: {path}")

        self.variable = CodeList("variable").parse_files(path / "variables")
        self.region = CodeList("region").parse_files(
            path / "regions", top_level_attr="hierarchy"
        )

    def validate(self, df: IamDataFrame) -> None:
        """Validate that the coordinates of `df` are defined in the codelists

        Parameters
        ----------
        df : IamDataFrame
            An IamDataFrame to be validated against the codelists of this nomenclature.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If `df` fails validation against any codelist.
        """
        validate(self, df)

    def to_excel(self, excel_writer, sheet_name="variable_definitions"):
        """Write the variable codelist to an Excel sheet

        Parameters
        ----------
        excel_writer : path-like, file-like, or :class:`pandas.ExcelWriter` object
            File path or existing ExcelWriter.
        sheet_name : str, optional
            Name of sheet which will contain the CodeList.
        """

        close = False
        if not isinstance(excel_writer, pd.ExcelWriter):
            close = True
            excel_writer = pd.ExcelWriter(excel_writer)

        # write definitions to sheet
        df = (
            pd.DataFrame.from_dict(self.variable, orient="index")
            .reset_index()
            .rename(columns={"index": "variable"})
            .drop(columns="file")
        )
        df.rename(columns={c: str(c).title() for c in df.columns}, inplace=True)

        write_sheet(excel_writer, sheet_name, df)

        # close the file if `excel_writer` arg was a file name
        if close:
            excel_writer.close()


def create_yaml_from_xlsx(source, target, sheet_name, col, attrs=[]):
    """Parses an xlsx file with a codelist and writes a yaml file

    Parameters
    ----------
    source : str, path, file-like object
        Path to Excel file with definitions (codelists).
    target : str, path, file-like object
        Path to save the parsed definitions as yaml file.
    sheet_name : str
        Sheet name of `source`.
    col : str
        Column from `sheet_name` to use as codes.
    attrs : list, optional
        Columns from `sheet_name` to use as attributes.

    """

    source = pd.read_excel(source, sheet_name=sheet_name)
    variable = source[[col] + attrs].set_index(col)
    variable.rename(columns={c: str(c).lower() for c in variable.columns}, inplace=True)

    with open(target, "w") as file:
        yaml.dump(variable.to_dict(orient="index"), file, default_flow_style=False)
