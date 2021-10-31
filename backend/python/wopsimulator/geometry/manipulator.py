import os
import math
import re
from typing import Union, List

import gmsh

from backend.python.wopsimulator.geometry.primitives import Num, Point, Line, Loop, Surface

GMSH_INITIALIZED = False


class TriSurface:
    """
    TriSurface class for models composed of multiple surfaces
    """

    def __init__(self):
        self.faces = []

    def produce(self, forced=False):
        """
        Produces faces using GMSH API
        :param forced: force produce the face
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        for face in faces:
            face.produce(forced)

    def withdraw(self):
        """
        Resets produced flag to allow to repopulate GMSH model
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        for face in faces:
            face.withdraw()

    def rotate(self, rotation: List[Num], center: List[Num]):
        """
        Rotates trisurface in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        rotated_points = []
        for face in faces:
            face_points = []
            for loop in face.loops:
                for line in loop.lines:
                    face_points += [point for point in line.points if point not in face_points]
            for point in list(set(face_points) - set(rotated_points)):
                point.rotate(rotation, center)
                rotated_points.append(point)

    def translate(self, coords: List[Num]):
        """
        Translates trisurface by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        translated_point = []
        for face in faces:
            face_points = []
            for loop in face.loops:
                for line in loop.lines:
                    face_points += [point for point in line.points if point not in face_points]
            for point in list(set(face_points) - set(translated_point)):
                point.translate(coords)
                translated_point.append(point)


class Box(TriSurface):
    """
    Box class (trisurface)
    """

    def __init__(self, dimensions: List[Num], location: List[Num] = (0, 0, 0)):
        """
        Box class initialization function
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        """
        super(Box, self).__init__()
        self.dimensions = dimensions
        self.location = location
        self.faces = {}
        self.create(dimensions, location)

    def create(self, dimensions, location):
        """
        Creates a box with certain dimensions and at a certain location
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        """
        p1 = Point(location[0], location[1], location[2])
        p2 = Point(location[0] + dimensions[0], location[1], location[2])
        p3 = Point(location[0] + dimensions[0], location[1] + dimensions[1], location[2])
        p4 = Point(location[0], location[1] + dimensions[1], location[2])
        p5 = Point(location[0], location[1], location[2] + dimensions[2])
        p6 = Point(location[0] + dimensions[0], location[1], location[2] + dimensions[2])
        p7 = Point(location[0] + dimensions[0], location[1] + dimensions[1], location[2] + dimensions[2])
        p8 = Point(location[0], location[1] + dimensions[1], location[2] + dimensions[2])

        l1 = Line(p1, p2)
        l2 = Line(p2, p3)
        l3 = Line(p4, p3)
        l4 = Line(p1, p4)

        l5 = Line(p5, p6)
        l6 = Line(p6, p7)
        l7 = Line(p8, p7)
        l8 = Line(p5, p8)

        l9 = Line(p1, p5)
        l10 = Line(p2, p6)
        l11 = Line(p3, p7)
        l12 = Line(p4, p8)

        ll1 = Loop([l1, l2, -l3, -l4])  # bottom
        ll2 = Loop([l8, l7, -l6, -l5])  # top
        ll3 = Loop([l4, l12, -l8, -l9])  # front
        ll4 = Loop([l10, l6, -l11, -l2])  # back
        ll5 = Loop([l9, l5, -l10, -l1])  # right
        ll6 = Loop([l3, l11, -l7, -l12])  # left

        self.faces.update({'bottom': Surface(ll1)})
        self.faces.update({'top': Surface(ll2)})
        self.faces.update({'front': Surface(ll3)})
        self.faces.update({'back': Surface(ll4)})
        self.faces.update({'right': Surface(ll5)})
        self.faces.update({'left': Surface(ll6)})

    def cut_surface(self, other):
        """
        Finds a proper face to cut a surface from
        :param other: surface class to cut
        """
        if not isinstance(other, Surface):
            raise AttributeError('Subtraction of surfaces can only be done between surfaces')
        matching_face = None
        other_x, other_y, other_z = other.get_used_coords()
        for name, face in self.faces.items():
            face_x, face_y, face_z = face.get_used_coords()
            if face_x == other_x or face_y == other_y or face_z == other_z:
                matching_face = name
        if matching_face:
            self.faces[matching_face].cut(other)
        else:
            raise ValueError('Tried to cut surface from box with no matching coordinates')

    def get_used_coords(self):
        """
        Determines the coordinates used by the box
        :return: sets for each coordinate [x, y, z]
        """
        faces_x, faces_y, faces_z = set(), set(), set()
        for face in self.faces.values():
            face_x, face_y, face_z = face.get_used_coords()
            faces_x = faces_x | face_x
            faces_y = faces_y | face_y
            faces_z = faces_z | face_z
        return faces_x, faces_y, faces_z


class STL(TriSurface):
    """
    STL class (trisurface) for imported STL models
    """

    def __init__(self, faces):
        """
        STL class initialization function
        :param faces: STL surfaces that compose a model
        """
        super(STL, self).__init__()
        self.faces = faces


class Model:
    """
    Geometric model class
    """
    _surface_type = 'surface'
    _box_type = 'box'
    _stl_type = 'stl'
    _model_types = [
        _surface_type,
        _box_type,
        _stl_type
    ]

    def __init__(self, name: str, model_type: str, dimensions: List[Num] = (0, 0, 0),
                 location: List[Num] = (0, 0, 0), rotation: List[Num] = (0, 0, 0),
                 facing_zero=True, stl_path: str = None):
        """
        Initializes a Model class
        :param name: name of a model, used for file naming and boundaries
        :param model_type: ['surface', 'box', 'stl']
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param stl_path: path to STL model, used for model_type = 'stl'
        """
        if model_type not in self._model_types:
            raise TypeError(f'Geometry model type {model_type} is not defined. '
                            f'Available model types are: {self._model_types}')
        self.name = name
        self.model_type = model_type
        self.dimensions = dimensions
        self.location = location
        self.rotation = rotation
        self.center = []
        self._initialized = False
        self._produced = False
        self.geometry = None
        self.geometry = self._create_geometry_from_type(facing_zero=facing_zero, stl_path=stl_path)

    def _init(self):
        """
        Initializes GMSH (if not initialized) and current GMSH model
        """
        global GMSH_INITIALIZED
        # FIXME: replace for a common class variable
        if not GMSH_INITIALIZED:
            GMSH_INITIALIZED = True
            gmsh.initialize()
            gmsh.clear()
        if not self._initialized:
            gmsh.model.add(self.name)
            self._initialized = True

    def _finilize(self):
        """
        Finilizes work with GMSH API and closes it and current model
        """
        global GMSH_INITIALIZED
        if self._initialized:
            self._initialized = False
            gmsh.clear()
            gmsh.model.remove()
            if self.geometry:
                self.geometry.withdraw()
            self._produced = False
        if GMSH_INITIALIZED:
            GMSH_INITIALIZED = False
            gmsh.finalize()

    def _produce(self):
        """
        Produces geometry using GMSH API
        :return:
        """
        if self._initialized:
            gmsh.model.set_current(self.name)
            if not self._produced:
                self.geometry.produce()
                # self.model.withdraw()
                gmsh.model.geo.synchronize()
                # Generate the coarsest mesh possible as it doesnt matter
                # for surface mesh
                gmsh.model.mesh.setSize(gmsh.model.getEntities(0), 1000)
                gmsh.model.mesh.generate(2)
                self._produced = True
            else:
                gmsh.model.remove()
                gmsh.model.add(self.name)
                self.geometry.withdraw()
                self._produced = False
                self._produce()
        else:
            self._init()
            self._produce()

    @staticmethod
    def _get_centroid(points):
        """
        Get center of an arbitrary surface from its points
        :param points:
        :return: center coordinates [x, y, z]
        """
        length = len(points)
        sum_x = sum([p.coords.x for p in points])
        sum_y = sum([p.coords.y for p in points])
        sum_z = sum([p.coords.z for p in points])
        return round(sum_x / length, 5), round(sum_y / length, 5), round(sum_z / length, 5)

    def _create_geometry_from_type(self, facing_zero, stl_path):
        """
        Creates geometry from a type provided
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param stl_path: path to STL model, used for model_type = 'stl'
        :return: Geometry class, e.g., Surface, Box or STL
        """
        # TODO: split this ifs into separate method for code readability
        if self.model_type == self._surface_type:
            if all(self.dimensions):
                raise ValueError(f'Model type {self._surface_type} must be 2D. Check your dimensions')
            elif len([dim for dim in self.dimensions if dim]) <= 1:
                raise ValueError(f'Model type {self._surface_type} must be 2D. Check your dimensions')
            else:
                d = self.dimensions
                l = self.location
                p1 = Point(l[0], l[1], l[2])
                if not d[0]:
                    p2 = Point(l[0], l[1], l[2] + d[2])
                    p3 = Point(l[0], l[1] + d[1], l[2] + d[2])
                    p4 = Point(l[0], l[1] + d[1], l[2])
                    c = [l[0], l[1] + d[1] / 2, l[2] + d[2] / 2]
                elif not d[1]:
                    p2 = Point(l[0] + d[0], l[1], l[2])
                    p3 = Point(l[0] + d[0], l[1], l[2] + d[2])
                    p4 = Point(l[0], l[1], l[2] + d[2])
                    c = [l[0] + d[0] / 2, l[1], l[2] + d[2] / 2]
                else:
                    p2 = Point(l[0], l[1] + d[1], l[2])
                    p3 = Point(l[0] + d[0], l[1] + d[1], l[2])
                    p4 = Point(l[0] + d[0], l[1], l[2])
                    c = [l[0] + d[0] / 2, l[1] + d[1] / 2, l[2]]
                l1, l2, l3, l4 = Line(p1, p2), Line(p2, p3), Line(p3, p4), Line(p4, p1)
                if facing_zero:
                    ll = Loop([l1, l2, l3, l4])
                else:
                    ll = Loop([-l4, -l3, -l2, -l1])
                s = Surface(ll)
                s.rotate(self.rotation, c)
                self.center = c
                return s
        elif self.model_type == self._box_type:
            if not all(self.dimensions):
                raise ValueError(f'Model type {self._box_type} must be 3D. Check your dimensions')
            else:
                b = Box(self.dimensions, self.location)
                self.center = [self.location[0] + self.dimensions[0] / 2,
                               self.location[1] + self.dimensions[1] / 2,
                               self.location[2] + self.dimensions[2] / 2]
                b.rotate(self.rotation, self.center)
                return b
        elif self.model_type == self._stl_type:
            self._init()
            gmsh.merge(stl_path)
            # Works for finding all the points
            # angle = 20
            # curve_angle = -180
            angle = 80
            curve_angle = -90
            include_boundary = True
            force_parameterizable_patches = True
            gmsh.model.mesh.classify_surfaces(math.radians(angle), include_boundary,
                                              force_parameterizable_patches,
                                              math.radians(curve_angle))
            gmsh.model.mesh.createGeometry()
            surf_nums = [num for dim, num in gmsh.model.getEntities(2)]
            # Extract all point number and their coordinates from the geometry
            points = []
            for point_num in [num for dim, num in gmsh.model.get_entities(0)]:
                point_coord = list(gmsh.model.get_value(0, point_num, []))
                points.append([point_coord, Point(coords=point_coord)])
            # Check whether a point lays on a surface
            surfaces = {}
            for surf_num in surf_nums:
                surfaces.update({surf_num: {'points': [], 'outer_points': [], 'inner_points': []}})
                for point_coord, point in points:
                    closest_point_coords = list(gmsh.model.get_closest_point(2, surf_num, point_coord)[0])
                    # Check if point coordinates match a closest point on surface
                    if point_coord == closest_point_coords:
                        surfaces[surf_num]['points'].append(point)
                # Find contour of the surface
                surfaces[surf_num]['outer_points'] = self._find_contour(surfaces[surf_num]['points'])
                if (remaining_points := list(set(surfaces[surf_num]['points']) -
                                             set(surfaces[surf_num]['outer_points']))):
                    # Not the best implementation as if there is more than 1 surface - it wouldn't work as expected
                    surfaces[surf_num]['inner_points'] = self._find_contour(remaining_points)
                surfaces[surf_num].update({'lines': []})
                surfaces[surf_num].update({'surface': []})
                for i in range(n := len(surfaces[surf_num]['outer_points'])):
                    p1, p2 = surfaces[surf_num]['outer_points'][i], surfaces[surf_num]['outer_points'][(i + 1) % n]
                    l = Line(p1, p2)
                    surfaces[surf_num]['lines'].append(l if l.p1 == p1 else -l)
                    # l if l.p1 == p1 else -l
                surfaces[surf_num]['surface'] = Surface(Loop(surfaces[surf_num]['lines']))
                inner_lines = []
                for i in range(n := len(surfaces[surf_num]['inner_points'])):
                    l = Line(surfaces[surf_num]['inner_points'][i], surfaces[surf_num]['inner_points'][(i + 1) % n])
                    inner_lines.append(l)
                if inner_lines:
                    surfaces[surf_num]['surface'].cut(Surface(Loop(inner_lines)))
            self._finilize()
            return STL(faces=[s['surface'] for s in surfaces.values()])

    def _rotate_to_axis(self, points):
        """
        Rotates a surface as a collection of points to one of the planes, thus eliminating one coordinate
        :param points: surface points
        """
        # Find center of a surface
        center = self._get_centroid(points)
        # Find a highest point
        max_z = max([pnt.coords.z for pnt in points])
        # Get a vector end point
        v_end_p = [pnt for pnt in points if pnt.coords.z == max_z][0]

        # Find vector, starts at center and ends in point with maximum height
        vector = [v_end_p.coords.x - center[0], v_end_p.coords.y - center[1], v_end_p.coords.z - center[2]]

        # The vector is then tried to be matched to the zy plane
        # Rotate all points around z axis such that the vector is parallel to y axis
        rotation = [0, 0, math.pi / 2 - math.atan(vector[1] / vector[0])]
        for point in points:
            point.rotate(rotation, center, radians=True)

        # Recalculate the vector coordinates
        vector = [v_end_p.coords.x - center[0], v_end_p.coords.y - center[1], v_end_p.coords.z - center[2]]
        # Rotate all points around y axis such that the vector is parallel to x axis
        rotation = [0, -math.atan(vector[0] / vector[2]), 0]
        for point in points:
            point.rotate(rotation, center, radians=True)

        # Recalculate the vector coordinates
        vector = [v_end_p.coords.x - center[0], v_end_p.coords.y - center[1], v_end_p.coords.z - center[2]]
        # Rotate all points around x axis such that the vector is parallel to y axis
        rotation = [-math.atan(vector[1] / vector[2]), 0, 0]
        for point in points:
            point.rotate(rotation, center, radians=True)

        # FIXME: Above manipulations do not work properly at the time :)))
        #  For now, a workaround is to find an axis with a minimal difference (either x or y) and simply truncate it

        # Get the list of all coordinates
        x_lst = [pnt.coords.x for pnt in points]
        y_lst = [pnt.coords.y for pnt in points]
        z_lst = [pnt.coords.z for pnt in points]

        # Find lengths across all axis
        max_diff_x = max(x_lst) - min(x_lst)
        max_diff_y = max(y_lst) - min(y_lst)
        max_diff_z = max(z_lst) - min(z_lst)
        max_diff = [('x', max_diff_x), ('y', max_diff_y), ('z', max_diff_z)]

        # Find an axis with smallest difference and truncate it. Initially, z axis was also included, but it didnt give
        # the expected results...
        max_diff.sort(key=lambda val: val[1], reverse=True)
        trunc_coord = max_diff[2][0]
        trunc_coord = trunc_coord if trunc_coord != 'z' else max_diff[1][0]
        for point in points:
            point.coords[trunc_coord] = 0

    def _find_contour(self, points):
        """
        Finds a contour of a surface from its points
        :param points: surface points
        """
        # Find maximums and minimums
        max_x = max([point.coords.x for point in points])
        max_y = max([point.coords.y for point in points])
        max_z = max([point.coords.z for point in points])
        min_x = min([point.coords.x for point in points])
        min_y = min([point.coords.y for point in points])
        min_z = min([point.coords.z for point in points])
        maxs = {'x': max_x, 'y': max_y, 'z': max_z}
        mins = {'x': min_x, 'y': min_y, 'z': min_z}

        # Check which axis is common for a given surface
        common_x = all([1 if math.isclose(point.coords.x, max_x, abs_tol=0.5) else 0 for point in points])
        common_y = all([1 if math.isclose(point.coords.y, max_y, abs_tol=0.5) else 0 for point in points])
        common_z = all([1 if math.isclose(point.coords.z, max_z, abs_tol=0.5) else 0 for point in points])

        # Check if no axis is common
        if not any([common_x, common_y, common_z]):
            # Save original coords
            point_coords = {pnt.num: list(pnt.coords).copy() for pnt in points}
            # Rotate points such that one axis is constant
            self._rotate_to_axis(points)
            # Find contours
            contour_loop = self._find_contour(points)
            # Restore original coordinates
            for pnt in points:
                pnt.coords.x, pnt.coords.y, pnt.coords.z = point_coords[pnt.num][:]
            return contour_loop

        # Find candidates for each axis. The idea is to find points with minimum coordinates, starting from y, z and
        # then x
        if not common_y:
            candidates = [point for point in points if point.coords.y == min_y]
        else:
            candidates = points[:]
        if not common_z:
            candidates = [candidate for candidate in candidates
                          if candidate.coords.z == min([candidate.coords.z for candidate in candidates])]
        if not common_x:
            candidates = [candidate for candidate in candidates
                          if candidate.coords.x == min([candidate.coords.x for candidate in candidates])]

        contour_loop = candidates
        if common_x:
            a = ['y', 'z']
        elif common_y:
            a = ['x', 'z']
        else:
            a = ['x', 'y']
        contour_loop += [point for point in points if maxs[a[0]] >= point.coords[a[0]] > contour_loop[-1].coords[a[0]]
                         and point.coords[a[1]] <= contour_loop[-1].coords[a[1]]]
        contour_loop += [point for point in points if maxs[a[1]] >= point.coords[a[1]] > contour_loop[-1].coords[a[1]]
                         and point.coords[a[0]] >= contour_loop[-1].coords[a[0]]]
        contour_loop += [point for point in points if mins[a[0]] <= point.coords[a[0]] < contour_loop[-1].coords[a[0]]
                         and point.coords[a[1]] >= contour_loop[-1].coords[a[1]]]
        contour_loop += [point for point in points if mins[a[1]] <= point.coords[a[1]] < contour_loop[-1].coords[a[1]]
                         and point.coords[a[0]] <= contour_loop[-1].coords[a[0]] and point not in contour_loop]
        return contour_loop

    def rotate(self, rotation: List[Num]):
        """
        Rotates geometry
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        """
        self.geometry.rotate(rotation, self.center)

    def translate(self, coords: List[Num]):
        """
        Translates geometry by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        self.geometry.translate(coords)

    def show(self):
        """
        Display the geometry using GMSH
        """
        self._produce()
        gmsh.fltk.run()
        self._finilize()

    def save(self, dir_path: str):
        """
        Save a geometry as an STL file
        :param dir_path: path to directory to save to
        """
        self._produce()
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        file_path = f'{dir_path}/{self.name}.stl'
        gmsh.write(file_path)
        rename_solid_stl(file_path, self.name)
        self._finilize()


def rename_solid_stl(stl_path: str, name: str):
    """
    Renames the solid in an STL file
    :param stl_path: path to STL file
    :param name: name of solids
    """
    stl_path = stl_path if '.stl' in stl_path else f'{stl_path}.stl'
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f'Path {stl_path} does not exist')
    lines = open(stl_path, 'r').readlines()
    new_lines = []
    solid_pattern = re.compile(r'((end)?solid)')
    for line in lines:
        match = solid_pattern.match(line)
        if match:
            line = f'{match.group(1)} {name}\n'
        new_lines.append(line)
    with open(stl_path, 'w') as f:
        f.writelines(new_lines)


def combine_stls(dest_path: str, other_paths: Union[List[str], str]):
    """
    Combines multiple STL files to one
    :param dest_path: path to destination STL file
    :param other_paths: paths to STL files
    """
    dest_path = dest_path if '.stl' in dest_path else f'{dest_path}.stl'
    open(dest_path, 'w').close()
    other_paths = other_paths if isinstance(other_paths, list) else [other_paths]
    other_paths = [stl_path if '.stl' in stl_path else f'{stl_path}.stl' for stl_path in other_paths]
    for path in other_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f'Path {path} does not exist')
    with open(dest_path, 'a') as dest_f:
        for other_path in other_paths:
            with open(other_path, 'r') as other_f:
                dest_f.write(other_f.read())


def main():
    # box = Model('box name', 'stl', stl_path='box name.stl')
    # box.show()
    box = Model('box name', 'box', [4, 4, 4], location=[10, 0, 0])
    surface_right = Model('surface_right', 'surface', [2, 0, 2], location=[11, 0, 1])
    surface_left = Model('surface_left', 'surface', [2, 0, 2], location=[11, 4, 1])
    # box.show()
    box.geometry.cut_surface(surface_right.geometry)
    box.geometry.cut_surface(surface_left.geometry)
    # box.geometry.faces['right'].cut(surface.geometry)
    # box.geometry.faces['front'].cut(surface.geometry)
    # # box.show()
    # # box.translate([0, 0, 100])
    # # box.show()
    # box.rotate([45, 45, 45])
    box.show()
    # # box.rotate([0, 0, -45])
    # # box.rotate([0, -45, 0])
    # # box.rotate([-45, 0, 0])
    # # box.show()
    # box.save()
    # combine_stls('box_1.stl', 'heater.stl')


if __name__ == '__main__':
    main()
