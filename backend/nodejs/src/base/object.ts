/**
 * Object module.
 *
 * @file   Contains an AbstractObject class that is used by simulated Phyngs in this application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractThing} from './thing';
import {Coordinates, ObjectProps} from './interfaces';
import {responseIsSuccessful} from "./helpers";
import {reqGet, reqPatch, reqDelete} from './axios-requests';

/**
 * An abstract object.
 *
 * Abstract class used by simulated Phyngs things in this application.
 * @class AbstractObject
 * @abstract
 */
export abstract class AbstractObject extends AbstractThing {
    /** Name of the case an object is assigned to. */
    protected caseName: string;
    /** Object location. */
    protected _location: Coordinates;
    /** Object name. */
    public _name: string;
    /** Object type, e.g., "sensor", "heater", etc. */
    protected _type: string;

    protected constructor(host: string, wot: WoT.WoT, tm: any, caseName: string, props: ObjectProps) {
        // Base URL cannot be yet set in node-wot,
        // thus a case name is added to a things model title
        tm.title = `${caseName}-${props.name}`
        super(host, wot, tm);
        this._name = props.name;
        this._type = props.type;
        this._location = 'location' in props && props.location ? props.location : [0, 0, 0];
        this.caseName = caseName;
        this.couplingUrl = `${this.host}/case/${this.caseName}/object/${this._name}`;
    }

    /**
     * Gets Phyng object name
     * @return {string} name of a Phyng object
     */
    public get name(): string {
        return this._name;
    }

    /**
     * Gets Phyng object type
     * @return {string} type of a Phyng object
     */
    public get type(): string {
        return this._type;
    }

    /**
     * Gets Phyng object location
     * @return {Coordinates} location of a Phyng object
     */
    public get location(): Coordinates {
        return this._location;
    }

    /**
     * Sets object location.
     * @param {Coordinates} location: location to set.
     * @async
     */
    public async setLocation(location: Coordinates): Promise<void> {
        this._location = location;
        let response = await reqPatch(`${this.couplingUrl}`, { location });
        if (response.status / 100 !== 2) {
            console.error(response.data);
        }
    }

    /**
     * Gets object parameters from a simulation server.
     * @return {Promise<any>} Object parameters from simulator.
     * @async
     */
    protected async getParamsFromSimulation(): Promise<any> {
        let response = await reqGet(`${this.couplingUrl}`);
        if (this._name in response.data) {
            return response.data[this._name];
        }
        return {};
    }

    /**
     * Updates object parameters from a simulation server.
     * @async
     */
    public async updateParams(): Promise<void> {
        let objectParams = await this.getParamsFromSimulation();
        this._location = objectParams.location;
    }

    public async destroy(): Promise<void> {
        let response = await reqDelete(this.couplingUrl);
        if (responseIsSuccessful(response.status)) {
            await super.destroy();
        }
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('type', async () => this.type);
        this.thing.setPropertyReadHandler('location', async () => this.location);
        this.thing.setPropertyWriteHandler('location', async (location) =>
            await this.setLocation(location)
        );
    }
}
