import math
from typing import Union, List

import gmsh

Num = Union[int, float, None]


class Coords:
    """
    Coordinates class, allows to access coordinates as an array or by individual elements [x, y, z]
    """

    def __init__(self, x: Num = None, y: Num = None, z: Num = None, coords: List[Num] = None):
        """
        Initialization function either x, y and z coordinates or array of coordinates must be provided
        :param x: x coordinate, number
        :param y: y coordinate, number
        :param z: z coordinate, number
        :param coords: coordinates array [x, y, z]
        """
        coords = coords if coords is not None else [x, y, z]
        if None in coords:
            raise AttributeError('Wrong arguments were provided to class Coords')
        if len(coords) != 3:
            raise AttributeError('Wrong number of arguments was provided to class Coords')
        coords = [float(c) for c in coords]
        self._x, self._y, self._z = coords
        self._coords = coords

    @property
    def x(self):
        """
        X coordinate getter
        :return: x
        """
        return self._x

    @x.setter
    def x(self, val: Num):
        """
        X coordinate setter
        :param val: value to set
        """
        self._x = val
        self._coords[0] = val

    @property
    def y(self):
        """
        Y coordinate getter
        :return: y
        """
        return self._y

    @y.setter
    def y(self, val: Num):
        """
        Y coordinate setter
        :param val: value to set
        """
        self._y = val
        self._coords[1] = val

    @property
    def z(self):
        """
        Z coordinate getter
        :return: z
        """
        return self._z

    @z.setter
    def z(self, val: Num):
        """
        Z coordinate setter
        :param val: value to set
        """
        self._z = val
        self._coords[2] = val

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.__dict__[f'_{item}']
        return self._coords[item]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.__dict__[f'_{key}'] = value
            return
        self._coords[key] = value

    def __iter__(self):
        return iter(self._coords)

    def __str__(self):
        return f'({self.x}, {self.y}, {self.z})'


class Point:
    """
    Point class with coordinates [x, y, z]
    """
    _instances = []
    _locations = []
    _numbers = []
    _current_number = 0
    _inst_number = 0

    def __new__(cls, x: Num = None, y: Num = None, z: Num = None, coords: List[Num] = None):
        """
        Point class creator
        :param x: x coordinate, number
        :param y: y coordinate, number
        :param z: z coordinate, number
        :param coords: coordinates array [x, y, z]
        """
        coords = coords if coords is not None else [x, y, z]
        if coords in cls._locations:
            idx = cls._locations.index(coords)
            cls._inst_number = idx
            return cls._instances[idx]
        instance = super(Point, cls).__new__(cls)
        cls._instances.append(instance)
        cls._locations.append(coords)
        cls._current_number += 1
        cls._numbers.append(cls._current_number)
        cls._inst_number = cls._current_number
        return instance

    def __init__(self, x: Num = None, y: Num = None, z: Num = None, coords: List[Num] = None):
        """
        Point class initialization function, either x, y and z coordinates or array of coordinates must be provided
        :param x: x coordinate, number
        :param y: y coordinate, number
        :param z: z coordinate, number
        :param coords: coordinates array [x, y, z]
        """
        self.coords = Coords(x, y, z, coords)
        self.num = self._inst_number
        self._produced = False

    def produce(self, forced=False):
        """
        Produces points using GMSH API
        :param forced: force produce the point
        """
        if not self._produced or forced:
            gmsh.model.geo.add_point(self.coords.x, self.coords.y, self.coords.z, tag=self.num)
            gmsh.model.geo.synchronize()
            self._produced = True

    def withdraw(self):
        """
        Resets produced flag to allow to repopulate GMSH model
        """
        self._produced = False

    def rotate(self, rotation: List[Num], center: List[Num], radians=False):
        """
        Rotates point in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        :param radians: flag to accept radians instead of degrees
        """
        old_coords = self.coords[:]
        rotated_vector = Coords(0, 0, 0)
        # X Axis rotation
        if rotation[0]:
            vector = Coords(coords=[a - b for a, b in zip(self.coords, center)])
            angle = math.radians(rotation[0]) if not radians else rotation[0]
            rotated_vector.x = vector.x
            rotated_vector.y = vector.y * math.cos(angle) - vector.z * math.sin(angle)
            rotated_vector.z = vector.y * math.sin(angle) + vector.z * math.cos(angle)
            self.coords.x, self.coords.y, self.coords.z = [round(a + b, 5) for a, b in zip(rotated_vector, center)]
        # Y Axis rotation
        if rotation[1]:
            vector = Coords(coords=[a - b for a, b in zip(self.coords, center)])
            angle = math.radians(rotation[1]) if not radians else rotation[1]
            rotated_vector.x = vector.x * math.cos(angle) + vector.z * math.sin(angle)
            rotated_vector.y = vector.y
            rotated_vector.z = - vector.x * math.sin(angle) + vector.z * math.cos(angle)
            self.coords.x, self.coords.y, self.coords.z = [round(a + b, 5) for a, b in zip(rotated_vector, center)]
        # Z Axis rotation
        if rotation[2]:
            vector = Coords(coords=[a - b for a, b in zip(self.coords, center)])
            angle = math.radians(rotation[2]) if not radians else rotation[2]
            rotated_vector.x = vector.x * math.cos(angle) - vector.y * math.sin(angle)
            rotated_vector.y = vector.x * math.sin(angle) + vector.y * math.cos(angle)
            rotated_vector.z = vector.z
            self.coords.x, self.coords.y, self.coords.z = [round(a + b, 5) for a, b in zip(rotated_vector, center)]
        self._locations[self._locations.index(old_coords)] = self.coords[:]

    def translate(self, coords):
        """
        Translates point by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        old_coords = self.coords[:]
        self.coords.x += coords[0]
        self.coords.y += coords[1]
        self.coords.z += coords[2]
        self._locations[self._locations.index(old_coords)] = coords


class Line:
    """
    Line class composed with two points
    """
    _instances = []
    _point_pairs = []
    _numbers = []
    _current_number = 0
    _inst_number = 0
    _inverse = False

    def __new__(cls, p1: Point = None, p2: Point = None, points: List[Point] = None):
        """
        Line class creator. Order of points defines line direction
        :param p1: first point
        :param p2: second point
        :param points: two points [p1, p2]
        """
        points = points if points is not None else [p1, p2]
        for idx, (point_1, point_2) in enumerate(cls._point_pairs):
            if point_1 in points and point_2 in points:
                instance = cls._instances[idx]
                cls._inverse = True
                cls._inst_number = instance.num
                return instance
        instance = super(Line, cls).__new__(cls)
        cls._instances.append(instance)
        cls._point_pairs.append(points)
        cls._current_number += 1
        cls._numbers.append(cls._current_number)
        cls._inst_number = cls._current_number
        return instance

    def __init__(self, p1: Point = None, p2: Point = None, points: List[Point] = None):
        """
        Line class initialization function, either p1 and p2 points or array of points must be provided.
        Order of points defines line direction
        :param p1: first point
        :param p2: second point
        :param points: points array [p1, p2]
        """
        points = points if points is not None else [p1, p2]
        if None in points:
            raise AttributeError('Wrong arguments were provided to class Line')
        if self.__class__._inverse:
            self.__class__._inverse = False
            points = [pp for num, pp in zip(self.__class__._numbers, self.__class__._point_pairs)
                      if num == self._inst_number][0]
        self.p1, self.p2 = points
        self.points = points
        self.num = self.__class__._inst_number
        self.opposite = False
        self._produced = False

    def __neg__(self):
        self.opposite = True
        return self

    def __call__(self, *args, **kwargs):
        if self.opposite:
            self.opposite = False
            return -self.num
        return self.num

    def produce(self, forced=False):
        """
        Produces line and its points using GMSH API
        :param forced: force produce the line and its points
        """
        if not self._produced or forced:
            for point in self.points:
                point.produce(forced)
            gmsh.model.geo.add_line(self.p1.num, self.p2.num, tag=self.num)
            gmsh.model.geo.synchronize()
            self._produced = True

    def withdraw(self):
        """
        Resets produced flag to allow to repopulate GMSH model
        """
        self._produced = False
        for point in self.points:
            point.withdraw()

    def rotate(self, rotation: List[Num], center: List[Num]):
        """
        Rotates line in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        """
        for point in self.points:
            point.rotate(rotation, center)

    def translate(self, coords: List[Num]):
        """
        Translates line by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        for point in self.points:
            point.translate(coords)


class Loop:
    """
    Loop class composed with multiple lines
    """
    _instances = []
    _lines = []
    _numbers = []
    _current_number = 0
    _inst_number = 0

    def __new__(cls, lines: List[Line] = None):
        """
        Loop class creator. Order of lines defines loop direction
        :param lines: two points [l1, l2, l3, ...]
        """
        for idx, used_lines in enumerate(cls._lines):
            if lines == used_lines:
                instance = cls._instances[idx]
                cls._inst_number = instance.num
                return instance
        instance = super(Loop, cls).__new__(cls)
        cls._instances.append(instance)
        cls._lines.append(lines)
        cls._current_number += 1
        cls._numbers.append(cls._current_number)
        cls._inst_number = cls._current_number
        return instance

    def __init__(self, lines: List[Line] = None):
        """
        Loop class initialization function. Order of lines defines loop direction
        :param lines: two points [l1, l2, l3, ...]
        """
        if None in lines:
            raise AttributeError('Wrong arguments were provided to class Loop')
        self.lines = lines
        self.line_sequence = [line() for line in lines]
        self.num = self._inst_number
        self._produced = False

    def produce(self, forced=False):
        """
        Produces loop and its lines using GMSH API
        :param forced: force produce the loop and its lines, points
        """
        if not self._produced or forced:
            for line in self.lines:
                line.produce(forced)
            gmsh.model.geo.add_curve_loop(self.line_sequence, tag=self.num)
            gmsh.model.geo.synchronize()
            self._produced = True

    def withdraw(self):
        """
        Resets produced flag to allow to repopulate GMSH model
        """
        self._produced = False
        for line in self.lines:
            line.withdraw()

    def rotate(self, rotation: List[Num], center: List[Num]):
        """
        Rotates loop in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        """
        for line in self.lines:
            line.rotate(rotation, center)

    def translate(self, coords: List[Num]):
        """
        Translates loop by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        for line in self.lines:
            line.translate(coords)


class Surface:
    """
    Surface class composed with single or multiple loops
    """
    _instances = []
    _loops = []
    _numbers = []
    _current_number = 0
    _inst_number = 0

    def __new__(cls, loop: Loop):
        """
        Surface class creator, class composed mainly of a single loop (contour)
        :param loop: line loop
        """
        for idx, used_loops in enumerate(cls._loops):
            if loop == used_loops:
                instance = cls._instances[idx]
                cls._inst_number = instance.num
                return instance
        instance = super(Surface, cls).__new__(cls)
        cls._instances.append(instance)
        cls._loops.append(loop)
        cls._current_number += 1
        cls._numbers.append(cls._current_number)
        cls._inst_number = cls._current_number
        return instance

    def __init__(self, loop: Loop):
        """
        Surface class initialization function, class composed mainly of a single loop (contour)
        :param loop: line loop
        """
        if loop is None:
            raise AttributeError('Wrong argument provided to class Surface')
        self.loops = [loop]
        self.num = self._inst_number
        self._produced = False

    def cut(self, other):
        """
        Cuts a surface from current current surface
        :param other: surface class
        """
        if not isinstance(other, self.__class__):
            raise AttributeError('Subtraction of surfaces can only be done between surfaces')
        # TODO: check if surface subtracted is smaller then self
        # TODO: check if surfaces lay in the same plane
        self.loops.extend(other.loops.copy())

    def produce(self, forced=False):
        """
        Produces surface and its loops using GMSH API
        :param forced: force produce the surface and its loops, lines, points
        """
        if not self._produced or forced:
            for loop in self.loops:
                loop.produce(forced)
            gmsh.model.geo.add_plane_surface([loop.num for loop in self.loops], tag=self.num)
            gmsh.model.geo.synchronize()
            self._produced = True

    def withdraw(self):
        """
        Resets produced flag to allow to repopulate GMSH model
        """
        self._produced = False
        for loop in self.loops:
            loop.withdraw()

    def rotate(self, rotation: List[Num], center: List[Num]):
        """
        Rotates loop in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        """
        for loop in self.loops:
            loop.rotate(rotation, center)

    def translate(self, coords: List[Num]):
        """
        Translates surface by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        for loop in self.loops:
            loop.translate(coords)
