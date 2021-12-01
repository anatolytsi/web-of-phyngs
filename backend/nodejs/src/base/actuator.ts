/**
 * Actuator object module.
 *
 * @file   Contains an Actuator class that is used by actuator node-things in this application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import axios from 'axios';
import {AbstractObject} from './object';
import {ActuatorPropsCreated, ActuatorPropsTemplate, Size, Vector} from './interfaces';

/**
 * An abstract actuator.
 *
 * Abstract class used by actuator node-things in this application.
 * @class Actuator
 * @abstract
 */
export abstract class Actuator extends AbstractObject implements ActuatorPropsCreated, ActuatorPropsTemplate {
    /** Actuator dimensions. */
    protected _dimensions: Size;
    /** Actuator rotation. */
    protected _rotation: Vector;
    /** Actuator template model name. */
    protected _template: string;

    protected constructor(host: string, wot: WoT.WoT, tm: any, caseName: string,
                          props: ActuatorPropsCreated | ActuatorPropsTemplate) {
        super(host, wot, tm, caseName, props);
        this._rotation = 'rotation' in props && props.rotation ? props.rotation : [0, 0, 0];
        this._dimensions = 'dimensions' in props ? props.dimensions : [0, 0, 0];
        this._template = 'template' in props ? props.template : '';
    }

    /**
     * Gets actuator Phyng dimensions
     * @return {Size} dimensions of an actuator Phyng.
     */
    public get dimensions(): Size {
        return this._dimensions;
    }

    /**
     * Sets actuator dimensions.
     * @param {Size} dimensions: dimensions to set.
     * @async
     */
    public async setDimensions(dimensions: Size): Promise<void> {
        this._dimensions = dimensions;
        let response = await axios.patch(`${this.couplingUrl}`, { dimensions });
        if (response.status / 100 !== 2) {
            console.error(response.data);
        }
    }

    /**
     * Gets actuator Phyng rotation
     * @return {Vector} rotation of an actuator Phyng.
     */
    public get rotation(): Vector {
        return this._rotation;
    }

    /**
     * Sets actuator rotation.
     * @param {Vector} rotation: rotation to set.
     * @async
     */
    public async setRotation(rotation: Vector): Promise<void> {
        this._rotation = rotation;
        let response = await axios.patch(`${this.couplingUrl}`, { rotation });
        if (response.status / 100 !== 2) {
            console.error(response.data);
        }
    }

    /**
     * Gets actuator Phyng template name.
     * @return {string} template name of an actuator Phyng.
     */
    public get template(): string {
        return this._template;
    }

    /**
     * Sets actuator template.
     * @param {string} template: template to set.
     * @async
     */
    public async setTemplate(template: string): Promise<void> {
        this._template = template;
        let response = await axios.patch(`${this.couplingUrl}`, { template });
        if (response.status / 100 !== 2) {
            console.error(response.data);
        }
    }

    protected addPropertyHandlers(): void {
        super.addPropertyHandlers();
        this.thing.setPropertyReadHandler('dimensions', async () => this.dimensions);
        this.thing.setPropertyWriteHandler('dimensions', async (dimensions) =>
            await this.setDimensions(dimensions)
        );
        this.thing.setPropertyReadHandler('rotation', async () => this.rotation);
        this.thing.setPropertyWriteHandler('rotation', async (rotation) =>
            await this.setRotation(rotation)
        );
        this.thing.setPropertyReadHandler('template', async () => this.dimensions);
        this.thing.setPropertyWriteHandler('template', async (template) =>
            await this.setTemplate(template)
        );
    }
}
