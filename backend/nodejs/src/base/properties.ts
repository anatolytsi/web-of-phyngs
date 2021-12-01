/**
 * Properties module.
 *
 * @file   Contains various Property classes used to define actuator interaction affordances.
 * @author Anatolii Tsirkunenko
 * @since  01.11.2021
 */
import axios from 'axios';
import {AnyUri} from 'wot-thing-description-types';
import {Vector} from './interfaces';

/**
 * Actuator heating properties.
 *
 * This class can be extended by an Actuator class to inherit heating properties.
 * @class HeatingProperties
 */
export class HeatingProperties {
    /**
     * Get temperature of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<number>} Temperature of an actuator.
     */
    public async getTemperature(couplingUrl: AnyUri): Promise<number> {
        let response = await axios.get(`${couplingUrl}/temperature`);
        return response.data;
    }

    /**
     * Set temperature of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {number} temperature Temperature to set on an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setTemperature(couplingUrl: AnyUri, temperature: number): Promise<any> {
        let response = await axios.post(`${couplingUrl}/temperature`, {value: temperature});
        return response.data
    }

    /**
     * Sets Web of Things temperature get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setTemperatureGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('temperature', async () =>
            await this.getTemperature(couplingUrl)
        );
    }

    /**
     * Sets Web of Things temperature set handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setTemperatureSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyWriteHandler('temperature', async (temperature) =>
            await this.setTemperature(couplingUrl, temperature)
        );
    }
}

/**
 * Actuator fluid velocity properties.
 *
 * This class can be extended by an Actuator class to inherit fluid velocity properties.
 * @class HeatingProperties
 */
export class VelocityProperties {
    /**
     * Get fluid velocity of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<Vector>} Fluid velocity of an actuator.
     */
    public async getVelocity(couplingUrl: AnyUri): Promise<Vector> {
        let response = await axios.get(`${couplingUrl}/velocity`);
        return response.data;
    }

    /**
     * Set fluid velocity of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {Vector} velocity Fluid velocity to set on an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setVelocity(couplingUrl: AnyUri, velocity: Vector): Promise<any> {
        let response = await axios.post(`${couplingUrl}/velocity`, {value: velocity});
        return response.data
    }

    /**
     * Sets Web of Things fluid velocity get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setVelocityGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('velocity', async () => {
            return await this.getVelocity(couplingUrl);
        });
    }

    /**
     * Sets Web of Things fluid velocity set handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setVelocitySetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyWriteHandler('velocity', async (velocity) => {
            await this.setVelocity(couplingUrl, velocity);
        });
    }
}

/**
 * Actuator openable properties.
 *
 * This class can be extended by an Actuator class to inherit openable properties.
 * @class HeatingProperties
 */
export class OpenableProperties {
    /**
     * Get open state of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<number>} Temperature of an actuator.
     */
    public async getOpen(couplingUrl: AnyUri): Promise<boolean> {
        let response = await axios.get(`${couplingUrl}/open`);
        return response.data;
    }

    /**
     * Open/close an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {boolean} open Flag to open/close an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setOpen(couplingUrl: AnyUri, open: boolean): Promise<any> {
        let response = await axios.post(`${couplingUrl}/open`, {value: open});
        return response.data
    }

    /**
     * Sets Web of Things actuator is opened get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setOpenedGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('opened', async () => {
            return await this.getOpen(couplingUrl);
        });
    }

    /**
     * Sets Web of Things actuator open handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setOpenSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setActionHandler('open', async () => {
            await this.setOpen(couplingUrl, true);
        });
    }

    /**
     * Sets Web of Things actuator close handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setCloseSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setActionHandler('close', async () => {
            await this.setOpen(couplingUrl, false);
        });
    }
}
