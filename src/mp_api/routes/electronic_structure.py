import base64
import zlib
from collections import defaultdict
from typing import List, Optional, Tuple, Union

import msgpack
from emmet.core.electronic_structure import (
    BSPathType,
    DOSProjectionType,
    ElectronicStructureDoc,
)
from monty.serialization import MontyDecoder
from mp_api.core.client import BaseRester, MPRestError
from pymatgen.analysis.magnetism.analyzer import Ordering
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.core import OrbitalType, Spin

import warnings


class ElectronicStructureRester(BaseRester[ElectronicStructureDoc]):

    suffix = "electronic_structure"
    document_model = ElectronicStructureDoc  # type: ignore
    primary_key = "material_id"

    def search_electronic_structure_docs(self, *args, **kwargs):  # pragma: no cover
        """
        Deprecated
        """

        warnings.warn(
            "MPRester.electronic_structure.search_electronic_structure_docs is deprecated. "
            "Please use MPRester.electronic_structure.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        band_gap: Optional[Tuple[float, float]] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        efermi: Optional[Tuple[float, float]] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        formula: Optional[Union[str, List[str]]] = None,
        is_gap_direct: bool = None,
        is_metal: bool = None,
        magnetic_ordering: Optional[Ordering] = None,
        num_elements: Optional[Tuple[int, int]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query electronic structure docs using a variety of search criteria.

        Arguments:
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): A formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            is_gap_direct (bool): Whether the material has a direct band gap.
            is_metal (bool): Whether the material is considered a metal.
            magnetic_ordering (Ordering): Magnetic ordering of the material.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ElectronicStructureDoc]) List of electronic structure documents
        """

        query_params = defaultdict(dict)  # type: dict

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if band_gap:
            query_params.update(
                {"band_gap_min": band_gap[0], "band_gap_max": band_gap[1]}
            )

        if efermi:
            query_params.update({"efermi_min": efermi[0], "efermi_max": efermi[1]})

        if magnetic_ordering:
            query_params.update({"magnetic_ordering": magnetic_ordering.value})

        if num_elements:
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if is_gap_direct is not None:
            query_params.update({"is_gap_direct": is_gap_direct})

        if is_metal is not None:
            query_params.update({"is_metal": is_metal})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )


class BandStructureRester(BaseRester):

    suffix = "electronic_structure/bandstructure"
    document_model = ElectronicStructureDoc  # type: ignore

    def search_bandstructure_summary(self, *args, **kwargs):  # pragma: no cover
        """
        Deprecated
        """

        warnings.warn(
            "MPRester.electronic_structure_bandstructure.search_bandstructure_summary is deprecated. "
            "Please use MPRester.electronic_structure_bandstructure.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        band_gap: Optional[Tuple[float, float]] = None,
        efermi: Optional[Tuple[float, float]] = None,
        is_gap_direct: bool = None,
        is_metal: bool = None,
        magnetic_ordering: Optional[Ordering] = None,
        path_type: BSPathType = BSPathType.setyawan_curtarolo,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query band structure summary data in electronic structure docs using a variety of search criteria.

        Arguments:
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            is_gap_direct (bool): Whether the material has a direct band gap.
            is_metal (bool): Whether the material is considered a metal.
            magnetic_ordering (Ordering): Magnetic ordering of the material.
            path_type (BSPathType): k-path selection convention for the band structure.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ElectronicStructureDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ElectronicStructureDoc]) List of electronic structure documents
        """

        query_params = defaultdict(dict)  # type: dict

        query_params["path_type"] = path_type.value

        if band_gap:
            query_params.update(
                {"band_gap_min": band_gap[0], "band_gap_max": band_gap[1]}
            )

        if efermi:
            query_params.update({"efermi_min": efermi[0], "efermi_max": efermi[1]})

        if magnetic_ordering:
            query_params.update({"magnetic_ordering": magnetic_ordering.value})

        if is_gap_direct is not None:
            query_params.update({"is_gap_direct": is_gap_direct})

        if is_metal is not None:
            query_params.update({"is_metal": is_metal})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )

    def get_bandstructure_from_task_id(self, task_id: str):
        """
        Get the band structure pymatgen object associated with a given task ID.

        Arguments:
            task_id (str): Task ID for the band structure calculation

        Returns:
            bandstructure (BandStructure): BandStructure or BandStructureSymmLine object
        """

        result = self._query_resource(
            criteria={"task_id": task_id, "_all_fields": True},
            suburl="object",
            use_document_model=False,
            num_chunks=1,
            chunk_size=1,
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No object found")

    def get_bandstructure_from_material_id(
        self,
        material_id: str,
        path_type: BSPathType = BSPathType.setyawan_curtarolo,
        line_mode=True,
    ):
        """
        Get the band structure pymatgen object associated with a Materials Project ID.

        Arguments:
            materials_id (str): Materials Project ID for a material
            path_type (BSPathType): k-point path selection convention
            line_mode (bool): Whether to return data for a line-mode calculation

        Returns:
            bandstructure (Union[BandStructure, BandStructureSymmLine]): BandStructure or BandStructureSymmLine object
        """

        es_rester = ElectronicStructureRester(
            endpoint=self.base_endpoint, api_key=self.api_key
        )

        if line_mode:
            bs_data = es_rester.get_data_by_id(
                document_id=material_id, fields=["bandstructure"]
            ).bandstructure

            if bs_data is None:
                raise MPRestError(
                    "No {} band structure data found for {}".format(
                        path_type.value, material_id
                    )
                )
            else:
                bs_data = bs_data.dict()

            if bs_data.get(path_type.value, None):
                bs_task_id = bs_data[path_type.value]["task_id"]
            else:
                raise MPRestError(
                    "No {} band structure data found for {}".format(
                        path_type.value, material_id
                    )
                )
        else:
            bs_data = es_rester.get_data_by_id(
                document_id=material_id, fields=["dos"]
            ).dos

            if bs_data is None:
                raise MPRestError(
                    "No uniform band structure data found for {}".format(material_id)
                )
            else:
                bs_data = bs_data.dict()

            if bs_data.get("total", None):
                bs_task_id = bs_data["total"]["1"]["task_id"]
            else:
                raise MPRestError(
                    "No uniform band structure data found for {}".format(material_id)
                )

        bs_obj = self.get_bandstructure_from_task_id(bs_task_id)

        if bs_obj:
            b64_bytes = base64.b64decode(bs_obj[0], validate=True)
            packed_bytes = zlib.decompress(b64_bytes)
            json_data = msgpack.unpackb(packed_bytes, raw=False)
            data = MontyDecoder().process_decoded(json_data["data"])

            return data
        else:
            raise MPRestError("No band structure object found.")


class DosRester(BaseRester):

    suffix = "electronic_structure/dos"
    document_model = ElectronicStructureDoc  # type: ignore

    def search_dos_summary(self, *args, **kwargs):  # pragma: no cover
        """
        Deprecated
        """

        warnings.warn(
            "MPRester.electronic_structure_dos.search_dos_summary is deprecated. "
            "Please use MPRester.electronic_structure_dos.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        band_gap: Optional[Tuple[float, float]] = None,
        efermi: Optional[Tuple[float, float]] = None,
        element: Optional[Element] = None,
        magnetic_ordering: Optional[Ordering] = None,
        orbital: Optional[OrbitalType] = None,
        projection_type: DOSProjectionType = DOSProjectionType.total,
        spin: Spin = Spin.up,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query density of states summary data in electronic structure docs using a variety of search criteria.

        Arguments:
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            element (Element): Element for element-projected dos data.
            magnetic_ordering (Ordering): Magnetic ordering of the material.
            orbital (OrbitalType): Orbital for orbital-projected dos data.
            projection_type (DOSProjectionType): Projection type of dos data. Default is the total dos.
            spin (Spin): Spin channel of dos data. If non spin-polarized data is stored in Spin.up
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ElectronicStructureDoc]) List of electronic structure documents
        """

        query_params = defaultdict(dict)  # type: dict

        query_params["projection_type"] = projection_type.value
        query_params["spin"] = spin.value

        if element:
            query_params["element"] = element.value

        if orbital:
            query_params["orbital"] = orbital.value

        if band_gap:
            query_params.update(
                {"band_gap_min": band_gap[0], "band_gap_max": band_gap[1]}
            )

        if efermi:
            query_params.update({"efermi_min": efermi[0], "efermi_max": efermi[1]})

        if magnetic_ordering:
            query_params.update({"magnetic_ordering": magnetic_ordering.value})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )

    def get_dos_from_task_id(self, task_id: str):
        """
        Get the density of states pymatgen object associated with a given calculation ID.

        Arguments:
            task_id (str): Task ID for the density of states calculation

        Returns:
            bandstructure (CompleteDos): CompleteDos object
        """

        result = self._query_resource(
            criteria={"task_id": task_id, "_all_fields": True},
            suburl="object",
            use_document_model=False,
            num_chunks=1,
            chunk_size=1,
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No object found")

    def get_dos_from_material_id(self, material_id: str):
        """
        Get the complete density of states pymatgen object associated with a Materials Project ID.

        Arguments:
            materials_id (str): Materials Project ID for a material

        Returns:
            dos (CompleteDos): CompleteDos object
        """

        es_rester = ElectronicStructureRester(
            endpoint=self.base_endpoint, api_key=self.api_key
        )

        dos_data = es_rester.get_data_by_id(
            document_id=material_id, fields=["dos"]
        ).dict()

        if dos_data["dos"]:
            dos_task_id = dos_data["dos"]["total"]["1"]["task_id"]
        else:
            raise MPRestError(
                "No density of states data found for {}".format(material_id)
            )

        dos_obj = self.get_dos_from_task_id(dos_task_id)
        if dos_obj:
            b64_bytes = base64.b64decode(dos_obj[0], validate=True)
            packed_bytes = zlib.decompress(b64_bytes)
            json_data = msgpack.unpackb(packed_bytes, raw=False)
            data = MontyDecoder().process_decoded(json_data["data"])
            return data
        else:
            raise MPRestError("No density of states object found.")
