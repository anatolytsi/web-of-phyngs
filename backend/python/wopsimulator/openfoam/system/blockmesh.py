import math
from typing import List

BLOCKMESH_DICT_FILE_TEMPLATE = r"""/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2106                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

scale   %d;

vertices
(
%s);

blocks
(
%s);

edges
(
%s);

defaultPatch
{
    type empty;
    name default;
}

boundary
(
%s);

// ************************************************************************* //
"""


class Vertex:
    """
    Vertex class with coordinates [x, y, z]
    """
    _instances = []
    _locations = []
    _numbers = []
    _current_number = -1
    _inst_number = 0

    def __new__(cls, x: float = None, y: float = None, z: float = None, coords: List[float] = None):
        """
        Vertex class creator
        :param x: x coordinate, number
        :param y: y coordinate, number
        :param z: z coordinate, number
        :param coords: coordinates array [x, y, z]
        """
        coords = coords if coords is not None else [x, y, z]
        if coords is None or None in coords:
            raise AttributeError('Wrong arguments were provided to class Vertex')
        if coords in cls._locations:
            idx = cls._locations.index(coords)
            cls._inst_number = idx
            return cls._instances[idx]
        instance = super(Vertex, cls).__new__(cls)
        cls._instances.append(instance)
        cls._locations.append(coords)
        cls._current_number += 1
        cls._numbers.append(cls._current_number)
        cls._inst_number = cls._current_number
        return instance

    def __init__(self, x: float = None, y: float = None, z: float = None, coords: List[float] = None):
        """
        Vertex class initialization function, either x, y and z coordinates or array of coordinates must be provided
        :param x: x coordinate, number
        :param y: y coordinate, number
        :param z: z coordinate, number
        :param coords: coordinates array [x, y, z]
        """
        self.coords = self._locations[self._inst_number]
        self.x, self.y, self.z = self.coords
        self.num = self._inst_number

    def __str__(self):
        return f'( {" ".join([str(coord) for coord in self.coords])} )\n'


class Block:
    """
    Block class with vertices [v0, v1, ...]
    """
    _instances = []
    _vertices = []
    _numbers = []
    _current_number = -1
    _inst_number = 0

    def __new__(cls, vertices: List[Vertex] = None, cells_in_direction: List[int] = (10, 10, 10),
                cell_expansion_ratios: List[int] = (1, 1, 1), name=None):
        """
        Block class creator
        :param vertices: vertices [v0, v1, ...]
        :param cells_in_direction: numbers of cells in each direction [x, y, z]
        :param cell_expansion_ratios: cell expansion ratios in directions [x, y, z]
        :param name: name of a block
        """
        if vertices is None or None in vertices:
            raise AttributeError('Wrong arguments were provided to class Block')
        if vertices in cls._vertices:
            idx = cls._vertices.index(vertices)
            cls._inst_number = idx
            return cls._instances[idx]
        instance = super(Block, cls).__new__(cls)
        cls._instances.append(instance)
        cls._vertices.append(vertices)
        cls._current_number += 1
        cls._numbers.append(cls._current_number)
        cls._inst_number = cls._current_number
        return instance

    def __init__(self, vertices: List[Vertex] = None, cells_in_direction: List[int] = (10, 10, 10),
                 cell_expansion_ratios: List[int] = (1, 1, 1), name=None):
        """
        Block class initialization function. Order of vertices defines direction
        :param vertices: vertices [v0, v1, ...]
        :param cells_in_direction: numbers of cells in each direction [x, y, z]
        :param cell_expansion_ratios: cell expansion ratios in directions [x, y, z]
        :param name: name of a block
        """
        self.vertices = vertices
        self.num = self._inst_number
        self.cells_in_direction = cells_in_direction
        self.cell_expansion_ratios = cell_expansion_ratios
        self.name = name

    def __str__(self):
        return f'hex ({" ".join([str(vertex.num) for vertex in self.vertices])}) ' \
               f'{self.name + " " if self.name is not None else ""}' \
               f'({" ".join([str(num) for num in self.cells_in_direction])}) simpleGrading ' \
               f'({" ".join([str(num) for num in self.cell_expansion_ratios])})\n'

    def get_dimensions(self):
        """
        Gets block dimensions
        :return: block dimensions [x, y, z]
        """
        x_min, x_max, y_min, y_max, z_min, z_max = 0, 0, 0, 0, 0, 0
        for vertex in self.vertices:
            if vertex.x < x_min:
                x_min = vertex.x
            elif vertex.x > x_max:
                x_max = vertex.x
            if vertex.y < y_min:
                y_min = vertex.y
            elif vertex.y > y_max:
                y_max = vertex.y
            if vertex.z < z_min:
                z_min = vertex.z
            elif vertex.z > z_max:
                z_max = vertex.z
        return x_max - x_min, y_max - y_min, z_max - z_min


class Edge:
    pass


class Boundary:
    pass


class BlockMeshDict:
    """BlockMesh dictionary file representation as a class"""

    def __init__(self, case_dir, mesh_quality: int = 50):
        """
        BlockMeshDict class initialization function
        :param case_dir: case directory
        :param mesh_quality: mesh quality in percents
        """
        self.scale = 1
        self._case_dir = case_dir
        self._mesh_quality = mesh_quality
        self.vertices = []
        self.blocks = []
        self.edges = []
        self.boundaries = []
        self._min_block_size = 0.1
        self._max_block_size = 0.7
        self._calculate_quality_coefficients()
        self._calculate_mesh_quality()

    def _calculate_quality_coefficients(self):
        self._avg_block_size = (self._min_block_size + self._max_block_size) / 2
        percents = [0, 50, 100]
        values = [self._max_block_size, self._avg_block_size, self._min_block_size]
        sum_of_mult = sum([x * y for x, y in zip(percents, values)])
        percents_sq = [math.pow(perc, 2) for perc in percents]
        percents_sq_sum = math.pow(sum(percents), 2)
        percents_sum_sq = sum(percents_sq)
        sum_percents = sum(percents)
        sum_values = sum(values)
        n = len(percents)
        # Linear regression coefficients
        self._quality_a = (sum_percents * sum_values - n * sum_of_mult) / (percents_sq_sum - n * percents_sum_sq)
        self._quality_b = (sum_percents * sum_of_mult - percents_sum_sq * sum_values) / \
                          (percents_sq_sum - n * percents_sum_sq)

    def _calculate_mesh_quality(self):
        self._calculate_quality_coefficients()
        if 0 > self._mesh_quality or self._mesh_quality > 100:
            raise ValueError(f'Mesh quality is defined in percentage '
                             f'(0%-100%), but {self._mesh_quality} was provided')
        self._block_size = self._quality_a * self._mesh_quality + self._quality_b
        for block in self.blocks:
            self._calculate_mesh(block)

    @property
    def mesh_quality(self):
        """Mesh quality getter"""
        return self._mesh_quality

    @mesh_quality.setter
    def mesh_quality(self, mesh_quality):
        """
        Mesh quality setter
        :param mesh_quality: mesh quality in percents
        """
        self._mesh_quality = mesh_quality
        self._calculate_mesh_quality()

    def _calculate_mesh(self, block):
        """
        Calculates block mesh according to given mesh quality
        :param block: block to calculate mesh for
        :return:
        """
        block.cells_in_direction = [int(dim // self._block_size) for dim in block.get_dimensions()]

    def add_box(self, min_coords: List[float] = None, max_coords: List[float] = None,
                cells_in_direction: List[int] = (10, 10, 10), cell_expansion_ratios: List[int] = (1, 1, 1), name=None):
        """
        Adds box to a blockMesh class
        :param min_coords: minimum coordinates
        :param max_coords: maximum coordinates
        :param cells_in_direction: numbers of cells in each direction [x, y, z]
        :param cell_expansion_ratios: cell expansion ratios in directions [x, y, z]
        :param name: name of a block
        """
        if min_coords is None and max_coords is None:
            raise ValueError(f'Max and min coords must be defined')
        v0 = Vertex(min_coords[0], min_coords[1], min_coords[2])
        v1 = Vertex(max_coords[0], min_coords[1], min_coords[2])
        v2 = Vertex(max_coords[0], max_coords[1], min_coords[2])
        v3 = Vertex(min_coords[0], max_coords[1], min_coords[2])
        v4 = Vertex(min_coords[0], min_coords[1], max_coords[2])
        v5 = Vertex(max_coords[0], min_coords[1], max_coords[2])
        v6 = Vertex(max_coords[0], max_coords[1], max_coords[2])
        v7 = Vertex(min_coords[0], max_coords[1], max_coords[2])
        vertices = [v0, v1, v2, v3, v4, v5, v6, v7]
        block = Block(vertices, cells_in_direction, cell_expansion_ratios, name)
        if block not in self.blocks:
            self.vertices.extend(vertices)
            self.blocks.append(block)
            dimensions = block.get_dimensions()
            self._min_block_size = 0.1 * max(dimensions) / 3
            self._max_block_size = 0.7 * max(dimensions) / 3
            self._calculate_mesh_quality()
            self._calculate_mesh(block)

    def save(self):
        """Saves a class as blockMeshDict"""
        vertices_str = ' ' * 4 + f'{" " * 4}'.join([str(vertex) for vertex in self.vertices]) if self.vertices else ''
        blocks_str = ' ' * 4 + f'{" " * 4}'.join([str(block) for block in self.blocks]) if self.blocks else ''
        edges_str = ' ' * 4 + f'{" " * 4}'.join([str(edge) for edge in self.edges]) if self.edges else ''
        boundaries_str = ' ' * 4 + f'{" " * 4}'.join([str(b) for b in self.boundaries]) if self.boundaries else ''
        file_output = BLOCKMESH_DICT_FILE_TEMPLATE % (self.scale, vertices_str, blocks_str, edges_str, boundaries_str)
        with open(f'{self._case_dir}/system/blockMeshDict', 'w') as f:
            f.writelines(file_output)


def main():
    block_mesh = BlockMeshDict('test.case')
    block_mesh.add_box([-1, -1, -1], [4, 5, 3.5], name='air')
    block_mesh.save()


if __name__ == '__main__':
    main()
