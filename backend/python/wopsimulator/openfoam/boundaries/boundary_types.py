GEOMETRIC_BOUNDARY_TYPES = [
    'empty',
    'processor',
    'symmetryPlane',
    'wedge'
]

GENERAL_BOUNDARY_TYPES = [
    'fixedValue',
    'fixedGradient',
    'mixed',
    'codedFixedValue',
    'uniformFixedValue',
    'zeroGradient',
    'calculated'
]

INLET_BOUNDARY_TYPES = [
    'outletInlet',
    'flowRateInletVelocity',
    'turbulentDigitalFilterInlet',
    'turbulentDFSEMInlet',
    'fanPressure',
    'turbulentIntensityKineticEnergyInlet',
    'turbulentMixingLengthDissipationRateInlet',
    'turbulentMixingLengthFrequencyInlet',
    'atmBoundaryLayerInletEpsilon',
    'atmBoundaryLayerInletK',
    'atmBoundaryLayerInletOmega',
    'atmBoundaryLayerInletVelocity',
    'atmBoundaryLayer'  # defined in a different way
]

OUTLET_BOUNDARY_TYPES = [
    'inletOutlet',
    'pressureInletOutletVelocity',
    'fanPressure',
    'totalPressure',
    'totalTemperature'
]

WALL_BOUNDARY_TYPES = [
    'noSlip',
    'translatingWallVelocity',
    'movingWallVelocity',
    'atmTurbulentHeatFluxTemperature',
    'atmAlphatkWallFunction',
    'atmEpsilonWallFunction',
    'atmNutkWallFunction',
    'atmNutUWallFunction',
    'atmNutWallFunction',
    'atmOmegaWallFunction',
    'epsilonWallFunction',
    'kLowReWallFunction',
    'kqRWallFunction',
    'nutkRoughWallFunction',
    'nutkWallFunction',
    'nutLowReWallFunction',
    'nutUBlendedWallFunction',
    'nutURoughWallFunction',
    'nutUSpaldingWallFunction',
    'nutUTabulatedWallFunction',
    'nutUWallFunction',
    'nutWallFunction',  # defined in a different way
    'omegaWallFunction',  # defined in a different way
    'compressible::alphatWallFunction',
    'compressible::epsilonWallFunction',
    'fixedFluxPressure',
]

COUPLED_BOUNDARY_TYPES = [
    'cyclicAMI',
    'cyclic',
    'fan',
    'compressible::turbulentTemperatureCoupledBaffleMixed',
]


class BoundaryType:
    type = ''
    types = []
    _registry = {}

    def __init_subclass__(cls, boundary, **kwargs):
        super().__init_subclass__(**kwargs)
        if boundary is None:
            raise ValueError(f'Incorrect class {cls.__name__} creation - boundary cannot be {boundary}.')
        cls._registry[boundary] = cls

    def __new__(cls, boundary, *args, **kwargs):
        if boundary not in (keys := cls._registry.keys()):
            raise ValueError(f'Incorrect boundary {boundary}. Possible boundaries are: {list(keys)}')
        subclass = cls._registry[boundary]
        obj = object.__new__(subclass)
        return obj

    def __get__(self, instance, owner):
        return instance.__dict__[self.type]

    def __set__(self, instance, boundary_type):
        if boundary_type not in self.types:
            raise ValueError(f'Incorrect boundary type {boundary_type} for {type(self).__name__}.\n'
                             f'Possible types are: {self.types}')
        instance.__dict__[self.type] = boundary_type

    def __delete__(self, instance):
        del instance.__dict__[self.type]

    def __set_name__(self, owner, boundary_type):
        self.type = boundary_type


class GeometricBoundaryType(BoundaryType, boundary='geometric'):
    types = GEOMETRIC_BOUNDARY_TYPES


class GeneralBoundaryType(BoundaryType, boundary='general'):
    types = GENERAL_BOUNDARY_TYPES


class InletBoundaryType(BoundaryType, boundary='inlet'):
    types = INLET_BOUNDARY_TYPES


class OutletBoundaryType(BoundaryType, boundary='outlet'):
    types = OUTLET_BOUNDARY_TYPES


class WallBoundaryType(BoundaryType, boundary='wall'):
    types = WALL_BOUNDARY_TYPES


class CoupledBoundaryType(BoundaryType, boundary='coupled'):
    types = COUPLED_BOUNDARY_TYPES


class BoundaryBase:
    def __str__(self):
        output_str = '\n{'
        list_of_attr = ['type']  # make it first in the list
        list_of_attr += [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))
                         if a != 'type' and a != 'is_uniform']
        uniform = ''
        if 'is_uniform' in dir(self):
            uniform = 'uniform ' if self.__getattribute__('is_uniform') else ''
        max_length = len(max(list_of_attr, key=len)) + 1

        for name in list_of_attr:
            value = self.__getattribute__(name)
            if value is None:
                continue
            if isinstance(value, list):
                value = '(' + ' '.join([str(val) for val in value]) + ')'
            output_str += f'\n{" " * 4}{name}{" " * (max_length - len(name))}' \
                          f'{uniform if "value" in name.lower() else ""}{value};'
        output_str += '\n}'
        return output_str

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        self.__dict__[key] = value


class GeometricBoundary(BoundaryBase):
    type = BoundaryType(boundary='geometric')

    def __init__(self,
                 boundary_type,
                 empty_instance=False):
        if not empty_instance:
            self.type = boundary_type


class GeneralBoundary(BoundaryBase):
    type = BoundaryType(boundary='general')

    def __init__(self,
                 # Shared (in some) stuff. Fixed value
                 boundary_type, value=None, is_uniform=False,
                 # Gradient
                 gradient=None,
                 # Mixed
                 ref_value=None, refGradient=None, valueFraction=None,
                 # Coded fixed value
                 redirectType=None, code=None,
                 # Uniform fixed value
                 uniformValue=None,
                 # Zero gradient
                 empty_instance=False
                 ):
        if not empty_instance:
            self.type = boundary_type
            if self.type == 'fixedValue':
                self._init_fixed_value_type(value, is_uniform)
            elif self.type == 'fixedGradient':
                self._init_fixed_gradient_type(gradient)
            elif self.type == 'mixed':
                self._init_fixed_mixed_type(ref_value, refGradient, valueFraction)
            elif self.type == 'codedFixedValue':
                self._init_coded_fixed_value_type(value, redirectType, code)
            elif self.type == 'uniformFixedValue':
                self._init_uniform_fixed_value_type(uniformValue)
            elif self.type == 'calculated':
                self._init_calculated_type(value, is_uniform)
            elif self.type == 'zeroGradient':
                pass

    def _init_fixed_value_type(self, value, is_uniform):
        if value is not None:
            self.value = value
            self.is_uniform = is_uniform
        else:
            raise ValueError(
                f'Missing argument for {self.type} general boundary type. Value is required.')

    def _init_fixed_gradient_type(self, gradient):
        pass

    def _init_fixed_mixed_type(self, refValue, refGradient, valueFraction):
        pass

    def _init_coded_fixed_value_type(self, value, redirectType, code):
        pass

    def _init_calculated_type(self, value, is_uniform):
        if value is not None:
            self.value = value
            self.is_uniform = is_uniform
        else:
            raise ValueError(f'Missing argument for {self.type} general boundary type. Value is required.')

    def _init_uniform_fixed_value_type(self, uniformValue):
        pass


class InletBoundary(BoundaryBase):
    type = BoundaryType(boundary='inlet')

    def __init__(self,
                 # Shared (in some) stuff
                 boundary_type, value=None, is_uniform=False, mapMethod=None, phi=None, U=None, C1=None,
                 # Outlet inlet type
                 outletValue=None,
                 # Flow rate
                 volumetricFlowRate=None, massFlowRate=None,
                 # Turbulent digital filter inlet
                 n=None, L=None, R=None, UMean=None, UBulk=None, fsm=None, Gaussian=None, fixSeed=None,
                 continuous=None, correctFlowRate=None, perturb=None, C1FSM=None, C2FSM=None,
                 # Turbulence DF-SEM
                 delta=None, nCellPerEddy=None,
                 # Fan pressure
                 file=None, outOfBounds=None, direction=None, p0=None,
                 # Turbulent intensity kinetic energy
                 intensity=None,
                 # Turbulent mixing length dissipation rate
                 mixingLength=None, k=None,
                 # Turbulent mixing length frequency
                 Cmu=None,
                 # atm boundary layer inlet epsilon/k/omega/velocity
                 flowDir=None, zDir=None, URef=None, ZRef=None, z0=None, d=None, kappa=None, initABL=None, C2=None,
                 empty_instance=False
                 ):
        if not empty_instance:
            self.type = boundary_type
            if self.type == 'outletInlet':
                self._init_inlet_outlet_type(outletValue, value, is_uniform, phi)
            elif self.type == 'flowRateInletVelocity':
                self._init_flow_rate_type(value, is_uniform, volumetricFlowRate, massFlowRate)
            elif self.type == 'turbulentDigitalFilterInlet':
                self._init_turbulent_digital_filter_type(n, L, R, UMean, UBulk, fsm, Gaussian, fixSeed, continuous,
                                                         correctFlowRate, perturb, C1FSM, C2FSM, mapMethod)
            elif self.type == 'turbulentDFSEMInlet':
                self._init_turbulent_dfsem_type(delta, nCellPerEddy, mapMethod, value, is_uniform)
            elif self.type == 'fanPressure':
                self._init_fan_pressure_type(file, outOfBounds, direction, p0, value, is_uniform, U, phi)
            elif self.type == 'turbulentIntensityKineticEnergyInlet':
                self._init_turbulent_intensity_kinetic_energy_type(intensity, value, is_uniform, U, phi)
            elif self.type == 'turbulentMixingLengthDissipationRateInlet':
                self._init_turbulent_mixing_length_dissipation_rate_type(mixingLength, value, is_uniform, k, phi)
            elif self.type == 'turbulentMixingLengthFrequencyInlet':
                self._init_turbulent_mixing_length_frequency_type(mixingLength, value, is_uniform, Cmu, k, phi)
            elif self.type in ['atmBoundaryLayerInletEpsilon', 'atmBoundaryLayerInletK',
                               'atmBoundaryLayerInletOmega', 'atmBoundaryLayerInletVelocity']:
                self._init_atm_boundary_layer_type(flowDir, zDir, URef, ZRef, z0, d, kappa, Cmu, initABL, phi, C1, C2)

    def _init_inlet_outlet_type(self, outletValue, value, is_uniform, phi):
        if outletValue is not None and value is not None:
            self.outletValue = outletValue
            self.value = value
            self.phi = phi
            self.is_uniform = is_uniform  # Maybe in the future it is needed to have uniform in one place only
        else:
            raise ValueError(
                f'Missing arguments for {self.type} inlet boundary type. Outlet value and value are'
                f'required, phi is optional.')

    def _init_flow_rate_type(self, value, is_uniform, volumetricFlowRate, massFlowRate):
        if value is not None and (volumetricFlowRate is not None or massFlowRate is not None):
            # These two are functions and don't know yet how to deal with them
            self.volumetricFlowRate = volumetricFlowRate
            self.massFlowRate = massFlowRate
            self.value = value
            self.is_uniform = is_uniform
        else:
            raise ValueError(
                f'Missing arguments for {self.type} inlet boundary type. Value is required and either mass flow rate or'
                f'volumetric flow rate functions must be defined')

    def _init_turbulent_digital_filter_type(self, n, L, R, UMean, UBulk, fsm, Gaussian, fixSeed, continuous,
                                            correctFlowRate, perturb, C1GSM, C2FSM, mapMethod):
        pass

    def _init_turbulent_dfsem_type(self, delta, nCellPerEddy, mapMethod, value, is_uniform):
        pass

    def _init_fan_pressure_type(self, file, outOfBounds, direction, p0, value, is_uniform, U, phi):
        pass

    def _init_turbulent_intensity_kinetic_energy_type(self, intensity, value, is_uniform, U, phi):
        pass

    def _init_turbulent_mixing_length_dissipation_rate_type(self, mixingLength, value, is_uniform, k, phi):
        pass

    def _init_turbulent_mixing_length_frequency_type(self, mixingLength, value, is_uniform, Cmu, k, phi):
        pass

    def _init_atm_boundary_layer_type(self, flowDir, zDir, URef, ZRef, z0, d, kappa, Cmu, initABL, phi, C1, C2):
        pass


class OutletBoundary(BoundaryBase):
    type = BoundaryType(boundary='outlet')

    def __init__(self,
                 # Shared (in some) stuff. Fixed value
                 boundary_type, value=None, is_uniform=False, U=None, p0=None, phi=None,
                 # Inlet outlet
                 inletValue=None,
                 # Pressure inlet outlet velocity
                 tangentialVelocity=None,
                 # Fan pressure
                 file=None, outOfBounds=None, direction=None,
                 # Total pressure
                 rho=None,
                 # Total Temperature
                 gamma=None, T0=None, psi=None,
                 empty_instance=False
                 ):
        if not empty_instance:
            self.type = boundary_type
            if self.type == 'inletOutlet':
                self._init_inlet_outlet_type(value, inletValue, phi, is_uniform)
            elif self.type == 'pressureInletOutletVelocity':
                self._init_pressure_inlet_outlet_velocity_type(value, tangentialVelocity, phi, is_uniform)
            elif self.type == 'fanPressure':
                self._init_fan_pressure_type(file, outOfBounds, direction, p0, value, is_uniform, U, phi)
            elif self.type == 'totalPressure':
                self._init_total_pressure_type(rho, p0, value, is_uniform, U, phi)
            elif self.type == 'totalTemperature':
                self._init_total_temperature_type(gamma, T0, U, phi, psi)

    def _init_inlet_outlet_type(self, value, inletValue, phi, is_uniform):
        if value is not None and inletValue is not None:
            self.value = value
            self.inlet_value = inletValue
            self.phi = phi
            self.is_uniform = is_uniform
        else:
            raise ValueError(
                f'Missing argument for {self.type} outlet boundary type. Value and inlet value are required, '
                f'optional phi.')

    def _init_pressure_inlet_outlet_velocity_type(self, value, tangentialVelocity, phi, is_uniform):
        if value is not None and tangentialVelocity is not None:
            self.value = value
            self.tangential_velocity = tangentialVelocity
            self.phi = phi
            self.is_uniform = is_uniform
        else:
            raise ValueError(
                f'Missing argument for {self.type} outlet boundary type. Value and tangential velocity are required, '
                f'optional phi.')

    def _init_fan_pressure_type(self, file, outOfBounds, direction, p0, value, is_uniform, U, phi):
        pass

    def _init_total_pressure_type(self, rho, p0, value, is_uniform, U, phi):
        pass

    def _init_total_temperature_type(self, gamma, T0, U, phi, psi):
        pass


class WallBoundary(BoundaryBase):
    type = BoundaryType(boundary='wall')

    def __init__(self,
                 # Shared (in some) stuff. Fixed value
                 boundary_type, value=None, is_uniform=False, U=None, p0=None, phi=None,
                 # Atm turbulent heat flux temperature
                 heatSource=None, alphaEff=None, Cp0=None, q=None, gradient=None,
                 # Atm alphat k wall function
                 Pr=None, Prt=None, z0=None, Cmu=None, kappa=None,
                 # Atm epsilon wall function
                 lowReCorrection=None,
                 # Atm nut k wall function
                 boundNut=None,
                 # Atm nut u wall function
                 # Atm nut wall function
                 z0Min=None,
                 # Atm omega wall function
                 # Epsilon wall function
                 blending=None, n=None,
                 # k low re wall function
                 Ceps2=None, Ck=None, Bk=None, C=None,
                 # kq r wall function
                 # nut k rough wall function
                 Ks=None, Cs=None,
                 # nut k wall function
                 # nut low re wall function
                 # nut u blended wall function
                 # nut u rough wall function
                 roughnessHeight=None, roughnessConstant=None, roughnessFactor=None, maxIter=None, tolerance=None,
                 # nut u spalding wall function
                 # nut u tabulated wall function
                 uPlusTable=None,
                 # nut wall function
                 E=None,
                 # omega wall function
                 beta1=None,
                 empty_instance=False
                 ):
        if not empty_instance:
            self.type = boundary_type
            if self.type == 'translatingWallVelocity':
                self._init_translating_wall_type(U)
            elif self.type == 'movingWallVelocity':
                self._init_moving_wall_velocity_type(value, is_uniform)
            elif self.type == 'atmTurbulentHeatFluxTemperature':
                self._init_atm_turb_heat_flux_temperature_type(value, is_uniform, heatSource, alphaEff, Cp0, q,
                                                               gradient)
            elif self.type == 'atmAlphatkWallFunction':
                self._init_atm_alpha_t_k_wall_type(value, is_uniform, Pr, Prt, z0, Cmu, kappa)
            elif self.type == 'atmEpsilonWallFunction':
                self._init_atm_epsilon_wall_type(z0, Cmu, kappa, lowReCorrection)
            elif self.type == 'atmNutkWallFunction':
                self._init_atm_nut_k_wall_type(z0, boundNut, Cmu, kappa)
            elif self.type == 'atmNutUWallFunction':
                self._init_atm_nut_u_wall_type(z0, boundNut, kappa)
            elif self.type == 'atmNutWallFunction':
                self._init_atm_nut_wall_type(z0Min, z0, kappa)
            elif self.type == 'atmOmegaWallFunction':
                self._init_atm_omega_wall_type(z0, Cmu, kappa)
            elif self.type == 'epsilonWallFunction':
                self._init_epsilon_wall_type(lowReCorrection, blending, n)
            elif self.type == 'kLowReWallFunction':
                self._init_k_low_re_wall_type(Ceps2, Ck, Bk, C)
            elif self.type == 'nutkRoughWallFunction':
                self._init_nut_k_rough_wall_type(Ks, Cs)
            elif self.type == 'nutUBlendedWallFunction':
                self._init_nut_u_blended_wall_type(n)
            elif self.type == 'nutURoughWallFunction':
                self._init_nut_u_rough_wall_type(roughnessHeight, roughnessConstant, roughnessFactor, maxIter,
                                                 tolerance)
            elif self.type == 'nutUSpaldingWallFunction':
                self._init_nut_u_spalding_wall_type(maxIter, tolerance)
            elif self.type == 'nutUTabulatedWallFunction':
                self._init_nut_u_tabulated_wall_type(uPlusTable)
            elif self.type == 'nutWallFunction':
                self._init_nut_u_wall_type(Cmu, kappa, E, blending, n, U)
            elif self.type == 'omegaWallFunction':
                self._init_omega_wall_type(beta1, blending, n)
            elif self.type == 'compressible::alphatWallFunction':
                self._init_compressible_alphat_wall_type(value, is_uniform)
            elif self.type == 'compressible::epsilonWallFunction':
                self._init_compressible_epsilon_wall_type(value, is_uniform)
            elif self.type == 'fixedFluxPressure':
                self._init_fixed_flux_pressure(value, is_uniform)

    def _init_translating_wall_type(self, U):
        pass

    def _init_moving_wall_velocity_type(self, value, is_uniform):
        pass

    def _init_atm_turb_heat_flux_temperature_type(self, value, is_uniform, heatSource, alphaEff, Cp0, q, gradient):
        pass

    def _init_atm_alpha_t_k_wall_type(self, value, is_uniform, Pr, Prt, z0, Cmu, kappa):
        pass

    def _init_atm_epsilon_wall_type(self, z0, Cmu, kappa, lowReCorrection):
        pass

    def _init_atm_nut_k_wall_type(self, z0, boundNut, Cmu, kappa):
        pass

    def _init_atm_nut_u_wall_type(self, z0, boundNut, kappa):
        pass

    def _init_atm_nut_wall_type(self, z0Min, z0, kappa):
        pass

    def _init_atm_omega_wall_type(self, z0, Cmu, kappa):
        pass

    def _init_epsilon_wall_type(self, lowReCorrection, blending, n):
        pass

    def _init_k_low_re_wall_type(self, Ceps2, Ck, Bk, C):
        pass

    def _init_nut_k_rough_wall_type(self, Ks, Cs):
        pass

    def _init_nut_u_blended_wall_type(self, n):
        pass

    def _init_nut_u_rough_wall_type(self, roughnessHeight, roughnessConstant, roughnessFactor, maxIter, tolerance):
        pass

    def _init_nut_u_spalding_wall_type(self, maxIter, tolerance):
        pass

    def _init_nut_u_tabulated_wall_type(self, uPlusTable):
        pass

    def _init_nut_u_wall_type(self, Cmu, kappa, E, blending, n, U):
        pass

    def _init_omega_wall_type(self, beta1, blending, n):
        pass

    def _init_compressible_alphat_wall_type(self, value, is_uniform):
        self.value = value
        self.is_uniform = is_uniform

    def _init_compressible_epsilon_wall_type(self, value, is_uniform):
        self.value = value
        self.is_uniform = is_uniform

    def _init_fixed_flux_pressure(self, value, is_uniform):
        self.value = value
        self.is_uniform = is_uniform


class CoupledBoundary(BoundaryBase):
    type = BoundaryType(boundary='wall')

    def __init__(self,
                 # Shared (in some) stuff. Fixed value
                 boundary_type, value=None, is_uniform=False, neighbourPatch=None, transform=None,
                 # Cyclic arbitrary mesh interface (AMI)
                 # Cyclic
                 # Fan
                 # compressible::turbulentTemperatureCoupledBaffleMixed
                 neighbourFieldName=None, kappaMethod=None, kappa=None, Tnbr=None,
                 empty_instance=False
                 ):
        if not empty_instance:
            self.type = boundary_type
            if self.type == 'cyclicAMI':
                self._init_cyclic_ami_type(neighbourPatch, transform)
            elif self.type == 'cyclic':
                self._init_cyclic_type(neighbourPatch, transform)
            elif self.type == 'compressible::turbulentTemperatureCoupledBaffleMixed':
                self._init_compressible_turb_temp_coupled_baffle_mixed(neighbourFieldName, kappaMethod, kappa,
                                                                       Tnbr, value, is_uniform)

    def _init_cyclic_ami_type(self, neighbourPatch, transform):
        pass

    def _init_cyclic_type(self, neighbourPatch, transform):
        pass

    def _init_compressible_turb_temp_coupled_baffle_mixed(self, neighbourFieldName, kappaMethod, kappa,
                                                          Tnbr, value, is_uniform):
        if value is not None and neighbourFieldName is not None and kappaMethod is not None \
                and kappa is not None and Tnbr is not None:
            self.value = value
            self.is_uniform = is_uniform
            self.neighbour_field_name = neighbourFieldName
            self.kappa_method = kappaMethod
            self.kappa = kappa
            self.Tnbr = Tnbr
        else:
            raise ValueError(
                f'Missing argument for {self.type} wall boundary type. Value, neighbour field name, kappa, kappa '
                f'method and Tnbr are required.')

# if __name__ == '__main__':
#     test = InletBoundary('outletInlet', outlet_value=[1, 2, 3], value=[1, 2, 3], is_uniform=True)
