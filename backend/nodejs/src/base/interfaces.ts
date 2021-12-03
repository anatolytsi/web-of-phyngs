/**
 * Common Object Interfaces.
 *
 * @file   Contains common interfaces used in the application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */

import {AnyUri} from "wot-thing-description-types";

/**
 * Keys to prevent mutation of a
 * fixed length array.
 */
type ArrayLengthMutationKeys = 'splice' | 'push' | 'pop' | 'shift' | 'unshift'

/**
 * Fixed length array type, values are
 * mutable, length is not.
 */
export type FixedLengthArray<T, L extends number, TObj = [T, ...Array<T>]> =
    Pick<TObj, Exclude<keyof TObj, ArrayLengthMutationKeys>>
    & {
    readonly length: L
    [I: number]: T
    [Symbol.iterator]: () => IterableIterator<T>
}

/** Coordinate type x, y, z */
export type Coordinates = FixedLengthArray<number, 3>;

/** Vector type x, y, z */
export type Vector = FixedLengthArray<number, 3>;

/** Size type x, y, z */
export type Size = FixedLengthArray<number, 3>;

/**
 * Object properties base interface, used as a
 * base for actuator base and sensor.
 */
interface ObjectPropsBase {
    name: string;
    type: string;
    /** Object location. */
    location?: Coordinates;
}

/**
 * Actuator base properties, used as a base for
 * actuators created by geometry and template.
 */
export interface ActuatorPropsBase extends ObjectPropsBase {
    /** Actuator geometry rotation. */
    rotation?: Vector;
}

/**
 * Created actuator properties, used by
 * actuators created using geometry.
 */
export interface ActuatorPropsCreated extends ActuatorPropsBase {
    /** Actuator geometry dimensions. */
    dimensions: Size;
}

/**
 * Template actuator properties, used by
 * actuators created using template.
 */
export interface ActuatorPropsTemplate extends ActuatorPropsBase {
    /** Actuator template name. */
    template: string;
}

/**
 * Type to combine various actuator
 * properties into a single type.
 */
export type ActuatorProps = ActuatorPropsCreated | ActuatorPropsTemplate;

/**
 * Sensor properties.
 */
export interface SensorProps extends ObjectPropsBase {
    /** Sensor field to monitor (e.g., "T"). */
    field: string;
}

/**
 * Type to combine actuator and sensor
 * properties into a single type.
 */
export type ObjectProps = ActuatorProps | SensorProps;

/**
 * Basic case Web of Phyngs parameters.
 */
export interface CaseParameters {
    /** Case name. */
    name: string,
    /** Case type. */
    type: string,
    /** Case mesh quality. */
    meshQuality?: number,
    /** Case result cleaning limit (0 - no cleaning). */
    cleanLimit?: number,
    /** Is case running in parallel. */
    parallel?: boolean
    /** Amount of cores to run in parallel. */
    cores?: number
}

/**
 * Named Hyperlink REFerences (HREFs).
 */
interface NamedHrefs {
    /** Thing name. */
    name: string;
    /** Thing HREFs. */
    hrefs: AnyUri[]
}

/**
 * Case Hyperlink REFerences (HREFs).
 */
export interface CaseHrefs extends NamedHrefs {
}

/**
 * Object Hyperlink REFerences (HREFs).
 */
export interface ObjectHrefs extends NamedHrefs {
    /** Object type */
    type: string
}
