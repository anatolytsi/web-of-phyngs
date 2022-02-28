/**
 * Conjugate Heat Transfer (CHT) behavior module.
 *
 * @file   Contains phyngs associated with CHT case and the case itself.
 * @author Anatolii Tsirkunenko
 * @since  01.12.2021
 */
import {use} from 'typescript-mix';
import {HeatingProperties, OpenableProperties, VelocityProperties} from '../base/properties'
import {Actuator} from '../base/actuator';
import {ActuatorProps, PhyngProps, PhysicalDescription, SensorProps} from '../base/interfaces';
import {newSensor} from '../base/sensor';
import {AbstractCase} from '../base/case';
import {reqPatch} from '../base/axios-requests';
import {chtPdSchema, validateSchema} from '../base/schemas';

/** Walls common TM. */
let wallsTm = require('../../tms/behavior/cht/chtWalls.model.json');
/** Heater common TM. */
let heaterTm = require('../../tms/behavior/cht/chtHeater.model.json');
/** Window common TM. */
let windowTm = require('../../tms/behavior/cht/chtWindow.model.json');
/** Door common TM. */
let doorTm = require('../../tms/behavior/cht/chtDoor.model.json');

/** Heater interface wrapper for
 * multiple class extension. */
interface Heater extends HeatingProperties {
}

/**
 * CHT heater Phyng class.
 *
 * Heater Phyng that is used in CHT case.
 * @class Heater
 */
class Heater extends Actuator {
    @use(HeatingProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...heaterTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
    }

    protected addEventHandlers() {
    }
}

/** Walls interface wrapper for
 * multiple class extension. */
interface Walls extends HeatingProperties {
}

/**
 * CHT walls Phyng class.
 *
 * Walls Phyng that is used in CHT case.
 * @class Walls
 */
class Walls extends Actuator {
    @use(HeatingProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...wallsTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
    }

    protected addEventHandlers() {
    }
}

/** Door interface wrapper for
 * multiple class extension. */
interface Door extends HeatingProperties, VelocityProperties, OpenableProperties {
}

/**
 * CHT door Phyng class.
 *
 * Door Phyng that is used in CHT case.
 * @class Door
 */
class Door extends Actuator {
    @use(HeatingProperties, VelocityProperties, OpenableProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...doorTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
        this.setVelocityGetHandler(this.thing, this.couplingUrl);
        this.setVelocitySetHandler(this.thing, this.couplingUrl);
        this.setOpenedGetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
        this.setOpenSetHandler(this.thing, this.couplingUrl);
        this.setCloseSetHandler(this.thing, this.couplingUrl);
    }

    protected addEventHandlers() {
    }
}

/** Window interface wrapper for
 * multiple class extension. */
interface Window extends HeatingProperties, VelocityProperties, OpenableProperties {
}

/**
 * CHT window Phyng class.
 *
 * Window Phyng that is used in CHT case.
 * @class Window
 */
class Window extends Actuator {
    @use(HeatingProperties, VelocityProperties, OpenableProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...windowTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
        this.setVelocityGetHandler(this.thing, this.couplingUrl);
        this.setVelocitySetHandler(this.thing, this.couplingUrl);
        this.setOpenedGetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
        this.setOpenSetHandler(this.thing, this.couplingUrl);
        this.setCloseSetHandler(this.thing, this.couplingUrl);
    }

    protected addEventHandlers() {
    }
}

/**
 * CHT object constructors for various
 * types of phyngs used in CHT case
 */
const chtObjectConstructors: { [type: string]: Function } = {
    heater: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Heater(host, wot, caseName, props),
    walls: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Walls(host, wot, caseName, props),
    window: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Window(host, wot, caseName, props),
    door: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Door(host, wot, caseName, props),
    sensor: (host: string, wot: WoT.WoT, caseName: string, props: SensorProps) => newSensor(host, wot, caseName, props)
};

/**
 * Conjugate Heat Transfer (CHT) case class.
 * @class ChtCase
 */
export class ChtCase extends AbstractCase {
    /** Background region material. */
    protected _background: string = 'air';

    /**
     * Gets background region material name.
     * @return {string} Background region material name.
     */
    public get background(): string {
        return this._background;
    }

    /**
     * Sets background region material name.
     * @param {string} background Background region material name to set.
     * @async
     */
    public async setBackground(background: string): Promise<void> {
        this._background = background;
        let response = await reqPatch(this.couplingUrl, {background});
        if (response.status / 100 !== 2) {
            console.error(response.data);
        }
    }

    /**
     * Updates CHT case phyngs from a simulation server.
     */
    public async updatePhyngs() {
        let objects = await this.getPhyngsFromSimulator();
        if (objects) {
            for (const object of objects) {
                this.addPhyngToDict(object);
            }
        }
    }

    /**
     * Validates Physical Description for CHT object creation.
     * @param {PhysicalDescription} pd Physical Description of an object.
     * @protected
     */
    protected validatePd(pd: PhysicalDescription): void {
        validateSchema(pd, chtPdSchema);
    }

    /**
     * Adds a new object to a dictionary of phyngs.
     * @param {PhyngProps} props Object properties.
     * @protected
     */
    protected addPhyngToDict(props: PhyngProps) {
        let objectConstructor = chtObjectConstructors[props.type];
        this.phyngs[props.name] = objectConstructor(this.host, this.wot, this.name, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.thing.setPropertyReadHandler('background', async () => this.background);
        this.thing.setPropertyWriteHandler('background', async (background) => {
            await this.setBackground(background);
        });
    }
}
