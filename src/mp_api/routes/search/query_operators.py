from enum import Enum
from typing import Optional, Literal
from fastapi import Query

from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from mp_api.routes.magnetism.models import MagneticOrderingEnum
from mp_api.routes.search.models import SearchStats

from scipy.stats import gaussian_kde
import numpy as np

from collections import defaultdict


class HasPropsEnum(Enum):
    magnetism = "magnetism"
    piezoelectric = "piezoelectric"
    dielectric = "dielectric"
    elasticity = "elasticity"
    surface_properties = "surface_properties"
    insertion_electrode = "insertion_electrode"
    bandstructure = "bandstructure"
    dos = "dos"
    xas = "xas"
    grain_boundaries = "grain_boundaries"
    eos = "eos"


class HasPropsQuery(QueryOperator):
    """
    Method to generate a query on whether a material has a certain property
    """

    def query(
        self,
        has_props: Optional[str] = Query(
            None,
            description="Comma-delimited list of possible properties given by HasPropsEnum to search for.",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if has_props:
            crit = {"has_props": {"$all": has_props.split(",")}}

        return {"criteria": crit}


class MaterialIDsSearchQuery(QueryOperator):
    """
    Method to generate a query on search docs using multiple material_id values
    """

    def query(
        self,
        material_ids: Optional[str] = Query(
            None, description="Comma-separated list of material_ids to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if material_ids:
            crit.update({"material_id": {"$in": material_ids.split(",")}})

        return {"criteria": crit}


class SearchIsStableQuery(QueryOperator):
    """
    Method to generate a query on whether a material is stable
    """

    def query(
        self,
        is_stable: Optional[bool] = Query(
            None, description="Whether the material is stable."
        ),
    ):

        crit = {}

        if is_stable is not None:
            crit["is_stable"] = is_stable

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("is_stable", False)]


class SearchMagneticQuery(QueryOperator):
    """
    Method to generate a query for magnetic data in search docs.
    """

    def query(
        self,
        ordering: Optional[MagneticOrderingEnum] = Query(
            None, description="Magnetic ordering of the material."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if ordering:
            crit["ordering"] = ordering.value

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("ordering", False)]


class SearchIsTheoreticalQuery(QueryOperator):
    """
    Method to generate a query on whether a material is theoretical
    """

    def query(
        self,
        theoretical: Optional[bool] = Query(
            None, description="Whether the material is theoretical."
        ),
    ):

        crit = {}

        if theoretical is not None:
            crit["theoretical"] = theoretical

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("theoretical", False)]


class SearchStatsQuery(QueryOperator):
    """
    Method to generate a query on search stats data
    """

    def __init__(self, search_doc):
        valid_numeric_fields = tuple(
            sorted(k for k, v in search_doc.__fields__.items() if v.type_ == float)
        )

        def query(
            field: Literal[valid_numeric_fields] = Query(  # type: ignore
                valid_numeric_fields[0],
                title=f"SearchDoc field to query on, must be a numerical field, "
                f"choose from: {', '.join(valid_numeric_fields)}",
            ),
            num_samples: Optional[int] = Query(
                None, title="If specified, will only sample this number of documents.",
            ),
            min_val: Optional[float] = Query(
                None,
                title="If specified, will only consider documents with field values "
                "greater than or equal to this minimum value.",
            ),
            max_val: Optional[float] = Query(
                None,
                title="If specified, will only consider documents with field values "
                "less than or equal to this minimum value.",
            ),
            num_points: int = Query(
                100, title="The number of values in the returned distribution."
            ),
        ) -> STORE_PARAMS:

            self.num_points = num_points
            self.min_val = min_val
            self.max_val = max_val

            if min_val or max_val:
                pipeline = [{"$match": {field: {}}}]  # type: list
                if min_val:
                    pipeline[0]["$match"][field]["$gte"] = min_val
                if max_val:
                    pipeline[0]["$match"][field]["$lte"] = max_val
            else:
                pipeline = []

            if num_samples:
                pipeline.append({"$sample": {"size": num_samples}})

            pipeline.append({"$project": {field: 1, "_id": 0}})

            return {"pipeline": pipeline}

        self.query = query

    def query(self):
        " Stub query function for abstract class "
        pass

    def post_process(self, docs):

        if docs:
            field = list(docs[0].keys())[0]

            num_points = self.num_points
            min_val = self.min_val
            max_val = self.max_val
            num_samples = len(docs)

            values = [d[field] for d in docs]
            if not min_val:
                min_val = min(values)
            if not max_val:
                max_val = max(values)

            kernel = gaussian_kde(values)

            distribution = list(
                kernel(
                    np.arange(min_val, max_val, step=(max_val - min_val) / num_points,)  # type: ignore
                )
            )

            median = float(np.median(values))
            mean = float(np.mean(values))

            response = SearchStats(
                field=field,
                num_samples=num_samples,
                min=min_val,
                max=max_val,
                distribution=distribution,
                median=median,
                mean=mean,
            )

        return [response]


# TODO:
# XAS and GB sub doc query operators
# Add weighted work function to data
# Add dimensionality to search endpoint
# Add "has_reconstructed" data
