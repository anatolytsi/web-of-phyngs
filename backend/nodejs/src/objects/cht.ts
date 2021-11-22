import {use} from 'typescript-mix';
import {AbstractCase, AbstractObject, ActuatorPropsCreated, ActuatorPropsTemplate, SensorProps} from '../things'
import {HeatingProperties, OpenableProperties, VelocityProperties} from './properties'
import axios from "axios";

interface Heater extends HeatingProperties {
}

class Heater extends AbstractObject {
    @use(HeatingProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, name: string) {
        let td = require('../../tms/cht/heater.json'); // Default TD
        super(host, wot, td, caseName, name);
    }

    protected addPropertyHandlers() {
        this.setTemperatureGetHandler(this.thing, this.base);
    }

    protected addActionHandlers() {
        this.setTemperatureSetHandler(this.thing, this.base);
    }

    protected addEventHandlers() {
    }
}

interface Walls extends HeatingProperties {
}

class Walls extends AbstractObject {
    @use(HeatingProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, name: string) {
        let td = require('../../tms/cht/walls.json'); // Default TD
        super(host, wot, td, caseName, name);
    }

    protected addPropertyHandlers() {
        this.setTemperatureGetHandler(this.thing, this.base);
    }

    protected addActionHandlers() {
        this.setTemperatureSetHandler(this.thing, this.base);
    }

    protected addEventHandlers() {
    }
}

interface Door extends HeatingProperties, VelocityProperties, OpenableProperties {
}

class Door extends AbstractObject {
    @use(HeatingProperties, VelocityProperties, OpenableProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, name: string) {
        let td = require('../../tms/cht/door.json'); // Default TD
        super(host, wot, td, caseName, name);
    }

    protected addPropertyHandlers() {
        this.setTemperatureGetHandler(this.thing, this.base);
        this.setVelocityGetHandler(this.thing, this.base);
        this.setOpenGetHandler(this.thing, this.base);
    }

    protected addActionHandlers() {
        this.setTemperatureSetHandler(this.thing, this.base);
        this.setVelocitySetHandler(this.thing, this.base);
        this.setOpenSetHandler(this.thing, this.base);
    }

    protected addEventHandlers() {
    }
}

interface Window extends HeatingProperties, VelocityProperties, OpenableProperties {
}

class Window extends AbstractObject {
    @use(HeatingProperties, VelocityProperties, OpenableProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, name: string) {
        let td = require('../../tms/cht/window.json'); // Default TD
        super(host, wot, td, caseName, name);
    }

    protected addPropertyHandlers() {
        this.setTemperatureGetHandler(this.thing, this.base);
        this.setVelocityGetHandler(this.thing, this.base);
        this.setOpenGetHandler(this.thing, this.base);
    }

    protected addActionHandlers() {
        this.setTemperatureSetHandler(this.thing, this.base);
        this.setVelocitySetHandler(this.thing, this.base);
        this.setOpenSetHandler(this.thing, this.base);
    }

    protected addEventHandlers() {
    }
}

const chtTypeObjectConstructors: {[key:string]: Function} = {
    heater: (host: string, wot: WoT.WoT, caseName: string, name: string) => new Heater(host, wot, caseName, name),
    walls: (host: string, wot: WoT.WoT, caseName: string, name: string) => new Walls(host, wot, caseName, name),
    window: (host: string, wot: WoT.WoT, caseName: string, name: string) => new Window(host, wot, caseName, name),
    door: (host: string, wot: WoT.WoT, caseName: string, name: string) => new Door(host, wot, caseName, name)
};

export class ChtCase extends AbstractCase {
    protected _background: string = 'fluid';

    // TODO: write Object assign for TMs and TM includes

    public get background() {
        return this._background;
    }

    public async setBackground(background: string) {
        this._background = background;
        await axios.patch(this.base, {background: background});
    }

    public async getObjects() {
        let objects = await AbstractCase.prototype.getObjects.call(this);
        if (objects) {
            for (const object of objects) {
                this.addObjectToDict(object);
            }
            // TODO: add existing objects here
        }
    }

    protected addObjectToDict(props: ActuatorPropsCreated | ActuatorPropsTemplate | SensorProps) {
        let objectConstructor = chtTypeObjectConstructors[props.type];
        this.objects[props.name] = objectConstructor(this.host, this.wot, this.name, props.name);
    }
}
