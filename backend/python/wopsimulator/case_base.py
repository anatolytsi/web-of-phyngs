import random
from abc import ABC

from geometry.manipulator import combine_stls
from openfoam.interface import OpenFoamInterface
from openfoam.system.snappyhexmesh import SnappyRegion, SnappyPartitionedMesh, SnappyCellZoneMesh


class OpenFoamCase(OpenFoamInterface, ABC):
    """OpenFOAM case base class"""

    def __init__(self, *args, **kwargs):
        super(OpenFoamCase, self).__init__(*args, **kwargs)
        self._objects = {}
        self._partitioned_mesh = None

    def _get_mesh_dimensions(self) -> list:
        """
        Gets minimums and maximums of all axis
        :return: list of min and max, e.g., [(x_min, x_max), ...]
        """
        all_x, all_y, all_z = set(), set(), set()
        for obj in self._objects.values():
            obj_x, obj_y, obj_z = obj.model.geometry.get_used_coords()
            all_x = all_x | obj_x
            all_y = all_y | obj_y
            all_z = all_z | obj_z
        min_coords = [min(all_x), min(all_y), min(all_z)]
        max_coords = [max(all_x), max(all_y), max(all_z)]
        return list(zip(min_coords, max_coords))

    def _find_location_in_mesh(self, minmax_coords) -> [int, int, int]:
        """
        Finds a location in mesh, which is within the dimensions of the mesh
        and is not inside any cell zone mesh
        :param minmax_coords: dimensions of the mesh
        :return: x, y, z coordinates
        """
        # Find the forbidden coordinates, i.e., all cell zones' coordinates
        forbidden_coords = [{'min': obj.model.location,
                             'max': [c1 + c2 for c1, c2 in zip(obj.model.location, obj.model.dimensions)]}
                            for obj in self._objects.values() if type(obj.snappy) == SnappyCellZoneMesh]
        point_found = False
        coords_allowed = [False for _ in range(len(forbidden_coords))]
        # If there are no forbidden coordinates
        coords_allowed = [True] if not coords_allowed else coords_allowed
        x, y, z = 0, 0, 0
        # Loop while proper coordinates are found
        while not point_found:
            # Take a random point between the dimensions for each coordinate
            x = round(random.uniform(minmax_coords[0][0] + 0.1, minmax_coords[0][1] - 0.1), 3)
            y = round(random.uniform(minmax_coords[1][0] + 0.1, minmax_coords[1][1] - 0.1), 3)
            z = round(random.uniform(minmax_coords[2][0] + 0.1, minmax_coords[2][1] - 0.1), 3)
            # For each forbidden coordinate, check that it does not lie inside any forbidden zone
            for idx, coords in enumerate(forbidden_coords):
                coords_allowed[idx] = not (coords['min'][0] < x < coords['max'][0] and
                                           coords['min'][1] < y < coords['max'][1] and
                                           coords['min'][2] < z < coords['max'][2])
            point_found = all(coords_allowed)
        return x, y, z

    def prepare_geometry(self):
        """Prepares each objects geometry"""
        for obj in self._objects.values():
            obj.prepare()

    def partition_mesh(self, partition_name: str):
        """
        Partitions mesh by producing a partitioned mesh out of partition regions
        :param partition_name: partitioned mesh name
        """
        regions = [obj.snappy for obj in self._objects.values() if type(obj.snappy) == SnappyRegion]
        region_paths = [f'{self.case_dir}/constant/triSurface/{region.name}.stl' for region in regions]
        combine_stls(f'{self.case_dir}/constant/triSurface/{partition_name}.stl', region_paths)
        self._partitioned_mesh = SnappyPartitionedMesh(partition_name, f'{partition_name}.stl')
        self._partitioned_mesh.add_regions(regions)

    def prepare_partitioned_mesh(self):
        """
        Prepares partitioned mesh, i.e., adds it to snappyHexMeshDict and
        adds background mesh to blockMeshDict
        """
        # Get all partitions
        partitions = [obj.snappy for obj in self._objects.values() if type(obj.snappy) == SnappyCellZoneMesh]
        partitions.insert(0, self._partitioned_mesh)
        # Add partitions to snappyHexMeshDict, get dimensions and find a location in mesh
        self.snappy_dict.add_meshes(partitions)
        minmax_coords = self._get_mesh_dimensions()
        self.snappy_dict.location_in_mesh = self._find_location_in_mesh(minmax_coords)
        # Create background mesh in blockMeshDict, which is bigger then the original dimensions
        blockmesh_min_coords = [coord[0] - 1 for coord in minmax_coords]
        blockmesh_max_coords = [coord[1] + 1 for coord in minmax_coords]
        self.blockmesh_dict.add_box(blockmesh_min_coords, blockmesh_max_coords, name=self._partitioned_mesh.name)

    def bind_boundary_conditions(self):
        """Binds boundary conditions to objects"""
        for obj in self._objects.values():
            obj.bind_region_boundaries(self.boundaries)