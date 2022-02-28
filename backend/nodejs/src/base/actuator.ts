/**
 * Actuator Phyng module.
 *
 * @file   Contains an Actuator class that is used by actuator node-things in this application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractPhyng} from './phyng';
import {ActuatorPropsCreated, ActuatorPropsTemplate, Size, Vector} from './interfaces';
import {responseIsUnsuccessful} from "./helpers";
import {reqPatch, reqPost} from './axios-requests';
const FormData = require('form-data');
const fs = require('fs');

/**
 * An abstract actuator Phyng.
 *
 * Abstract class used by actuator node-things in this application.
 * @class Actuator
 * @abstract
 */
export abstract class Actuator extends AbstractPhyng implements ActuatorPropsCreated, ActuatorPropsTemplate {
    /** Actuator dimensions. */
    protected _dimensions: Size;
    /** Actuator rotation. */
    protected _rotation: Vector;
    /** Actuator was created from custom STL model. */
    protected _custom: boolean;
    /** Actuator template model name. */
    protected _template: string;

    protected constructor(host: string, wot: WoT.WoT, tm: any, caseName: string,
                          props: ActuatorPropsCreated | ActuatorPropsTemplate) {
        super(host, wot, tm, caseName, props);
        this._rotation = 'rotation' in props && props.rotation ? props.rotation : [0, 0, 0];
        this._dimensions = 'dimensions' in props ? props.dimensions : [0, 0, 0];
        this._custom = 'url' in props;
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
        let response = await reqPatch(`${this.couplingUrl}`, { dimensions });
        if (responseIsUnsuccessful(response.status)) {
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
        let response = await reqPatch(`${this.couplingUrl}`, { rotation });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets flag indicating if Phyng
     * was created from custom STL.
     * @return {boolean} true if custom.
     */
    public get custom(): boolean {
        return this._custom;
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
        let response = await reqPatch(`${this.couplingUrl}`, { template });
        if (responseIsUnsuccessful(response.status)) {
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

    protected addActionHandlers() {
        this.thing.setActionHandler('uploadSTL', async (data, options) => {
            let formData = new FormData();
            let filename = data.match(/filename="(.*\.stl)"/)[1];
            let filePath = `${__dirname}/${filename}`;
            fs.writeFile(filePath, data.match(/(solid(.|\n)*endsolid\s.*)/gm)[0], () => {});
            formData.append('file', fs.createReadStream(filePath));
            await reqPost(`${this.couplingUrl}`, formData,
                {
                    headers: formData.getHeaders()
                });
            fs.unlinkSync(filePath)
        });
    }
}
