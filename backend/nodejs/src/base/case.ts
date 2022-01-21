/**
 * Case module.
 *
 * @file   Contains an AbstractCase class that is used as a base for all case types.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractThing} from './thing';
import {CaseParameters, ObjectHrefs, ObjectProps} from './interfaces';
import {AbstractObject} from './object';
import {responseIsSuccessful, responseIsUnsuccessful} from './helpers';
import {reqGet, reqPost, reqPatch, makeRequest} from './axios-requests';
import {AxiosResponse} from 'axios';

/** Case commands allowed in the simulator. */
type CaseCommand = 'run' | 'stop' | 'setup' | 'clean' | 'postprocess' | 'time';

interface CaseTime {
    "real": string,
    "simulation": string,
    "difference": number
}

/**
 * An abstract case.
 *
 * Abstract class used by all Web of Phyngs
 * simulation cases in this application.
 * @class AbstractCase
 * @abstract
 */
export abstract class AbstractCase extends AbstractThing implements CaseParameters {
    /** Case name. */
    protected _name: string;
    /** Case type. */
    protected _type: string = '';
    /** Case objects. */
    protected objects: { [name: string]: AbstractObject };
    /** Case mesh quality. */
    protected _meshQuality: number = 50;
    /** Case result cleaning limit (0 - no cleaning). */
    protected _cleanLimit: number = 0;
    /** Is case running in parallel. */
    protected _parallel: boolean = true;
    /** Amount of cores to run in parallel. */
    protected _cores: number = 4;
    /** Is case running in realtime. */
    protected _realtime: boolean = true;
    /** Case simulation end time. */
    protected _endtime: number = 1000;

    /**
     * Abstract method to add a new object
     * to a dictionary of objects. It must be
     * case type specific to account for various
     * types of objects.
     * @param {ObjectProps} props Object properties.
     * @protected
     */
    protected abstract addObjectToDict(props: ObjectProps): void;

    /**
     * Abstract method to update case objects
     * from a simulation server.
     */
    public abstract updateObjects(): void;

    constructor(host: string, wot: WoT.WoT, tm: any, name: string) {
        super(host, wot, tm);
        this._name = name;
        this.couplingUrl = `${this.host}/case/${this.name}`;
        this.objects = {};
        this.updateParams();
        this.updateObjects();
    }

    /**
     * Gets case name.
     * @return {string} name of a case.
     */
    public get name(): string {
        return this._name;
    }

    /**
     * Gets case type.
     * @return {string} type of a case.
     */
    public get type(): string {
        return this._type;
    }

    /**
     * Gets case mesh quality.
     * @return {number} case mesh quality.
     */
    public get meshQuality(): number {
        return this._meshQuality;
    }

    /**
     * Sets case mesh quality.
     * @param {number} meshQuality: mesh quality to set.
     * @async
     */
    public async setMeshQuality(meshQuality: number): Promise<void> {
        if (meshQuality > 0 && meshQuality <= 100) {
            this._meshQuality = meshQuality;
            await reqPatch(this.couplingUrl, {mesh_quality: meshQuality});
        } else {
            // TODO: error
            console.error(`Mesh quality should be in range 0..100, but ${meshQuality} was provided`)
        }
    }

    /**
     * Gets case cleaning limit.
     * @return {number} case cleaning limit.
     */
    public get cleanLimit(): number {
        return this._cleanLimit;
    }

    /**
     * Sets case result cleaning limit.
     * @param {number} cleanLimit: cleaning limit to set.
     * @async
     */
    public async setCleanLimit(cleanLimit: number): Promise<void> {
        if (cleanLimit < 0) {
            this._cleanLimit = cleanLimit;
            await reqPatch(this.couplingUrl, {clean_limit: cleanLimit});
        } else {
            // TODO: error
            console.error('Cleaning limit cannot be negative!')
        }
    }

    /**
     * Gets parallel flag.
     * @return {boolean} parallel flag.
     */
    public get parallel(): boolean {
        return this._parallel;
    }

    /**
     * Enable/disable case parallel solving.
     * @param {boolean} parallel: parallel flag.
     * @async
     */
    public async setParallel(parallel: boolean): Promise<void> {
        this._parallel = parallel;
        await reqPatch(this.couplingUrl, {parallel});
    }

    /**
     * Gets number of cores for parallel run.
     * @return {number} number of cores.
     */
    public get cores(): number {
        return this._cores;
    }

    /**
     * Sets case number of cores for parallel run.
     * @param {number} cores: number of cores.
     * @async
     */
    public async setCores(cores: number): Promise<void> {
        if (cores < 0) {
            this._cores = cores;
            await reqPatch(this.couplingUrl, {cores});
        } else {
            console.log('Number of cores cannot be negative!')
        }
    }

    /**
     * Gets realtime flag.
     * @return {boolean} realtime flag.
     */
    public get realtime(): boolean {
        return this._realtime;
    }

    /**
     * Enable/disable case realtime solving.
     * @param {boolean} realtime: realtime flag.
     * @async
     */
    public async setRealtime(realtime: boolean): Promise<void> {
        this._realtime = realtime;
        await reqPatch(this.couplingUrl, {realtime});
    }

    /**
     * Gets simulation endtime.
     * @return {number} simulation endtime.
     */
    public get endtime(): number {
        return this._endtime;
    }

    /**
     * Sets simulation end time.
     * @param {number} endtime: simulation endtime.
     * @async
     */
    public async setEndtime(endtime: number): Promise<void> {
        this._endtime = endtime;
        await reqPatch(this.couplingUrl, {endtime});
    }

    /**
     * Runs a case.
     * @async
     */
    public async run(): Promise<void> {
        await this.executeCmd('run');
    }

    /**
     * Stops a case.
     * @async
     */
    public async stop(): Promise<void> {
        await this.executeCmd('stop');
    }

    /**
     * Setups a case.
     * @async
     */
    public async setup(): Promise<void> {
        await this.executeCmd('setup');
    }

    /**
     * Cleans a case.
     * @async
     */
    public async clean(): Promise<void> {
        await this.executeCmd('clean');
    }

    /**
     * Post processes a case.
     * @async
     */
    public async postprocess(): Promise<void> {
        await this.executeCmd('postprocess');
    }

    /**
     * Returns the current time
     * parameters of a simulation.
     * @return {Promise<CaseTime>} Current time parameters of the simulation.
     */
    public async getTime(): Promise<CaseTime> {
        let data = await this.executeCmd('time', 'get');
        return {
            'real': data['real_time'],
            'simulation': data['simulation_time'],
            'difference': data['time_difference']
        };
    }

    /**
     * Updates case parameters from a simulation server.
     * @async
     */
    public async updateParams(): Promise<void> {
        let response = await reqGet(`${this.couplingUrl}`);
        let caseParams = response.data;
        this._meshQuality = caseParams.mesh_quality;
        this._cleanLimit = caseParams.clean_limit;
        this._parallel = caseParams.parallel;
        this._cores = caseParams.cores;
    }

    /**
     * Adds object with properties to simulation and instantiates a corresponding class.
     * @param {ObjectProps} props Object properties.
     * @async
     */
    public async addObject(props: ObjectProps): Promise<void> {
        let {name, ...data} = props;
        let response = await reqPost(`${this.couplingUrl}/object/${name}`, data);
        if (responseIsSuccessful(response.status)) {
            this.addObjectToDict(props);
        } else {
            throw Error(response.data);
        }
    }

    /**
     * Removes an object with a given name from a simulator.
     * @param {string} name Name of an object.
     */
    public async removeObject(name: string): Promise<void> {
        if (!(name in this.objects)) return;
        await this.objects[name].destroy();
        delete this.objects[name];
    }

    /**
     * Gets case objects with their HREFs.
     * @return {ObjectHrefs[]} Objects with names, types and HREFs
     */
    public getObjects(): ObjectHrefs[] {
        let objects: ObjectHrefs[] = [];
        if (this.objects) {
            for (const name in this.objects) {
                objects.push({name, type: this.objects[name].type, hrefs: this.objects[name].getHrefs()});
            }
        }
        return objects;
    }

    /**
     * Gets objects from a simulation.
     * @return {Promise<any>} Simulation objects.
     * @async
     * @protected
     */
    protected async getObjectsFromSimulator(): Promise<any> {
        let response = await reqGet(`${this.couplingUrl}/object`);
        return response.data;
    }

    /**
     * Executes a case command.
     * @param {CaseCommand} command Case command to execute.
     * @param {"get" | "post"} method Method to execute command with.
     * @async
     * @protected
     */
    protected async executeCmd(command: CaseCommand, method: 'get' | 'post' = 'post'): Promise<any> {
        let response: AxiosResponse = await makeRequest({method, url: `${this.couplingUrl}/${command}`});
        if (responseIsUnsuccessful(response.status)) {
            throw Error(response.data);
        }
        return response.data;
}

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('meshQuality', async () => this.meshQuality);
        this.thing.setPropertyReadHandler('cleanLimit', async () => this.cleanLimit);
        this.thing.setPropertyReadHandler('parallel', async () => this.parallel);
        this.thing.setPropertyReadHandler('cores', async () => this.cores);
        this.thing.setPropertyReadHandler('objects', async () => this.getObjects());
        this.thing.setPropertyReadHandler('time', async () => this.getTime());
        this.thing.setPropertyReadHandler('realtime', async () => this.realtime);
        this.thing.setPropertyReadHandler('endtime', async () => this.endtime);

        this.thing.setPropertyWriteHandler('meshQuality', async (meshQuality) => {
            await this.setMeshQuality(meshQuality);
        });
        this.thing.setPropertyWriteHandler('cleanLimit', async (cleanLimit) => {
            await this.setCleanLimit(cleanLimit);
        });
        this.thing.setPropertyWriteHandler('parallel', async (parallel) => {
            await this.setParallel(parallel);
        });
        this.thing.setPropertyWriteHandler('cores', async (cores) => {
            await this.setCores(cores);
        });
        this.thing.setPropertyWriteHandler('realtime', async (realtime) => {
            await this.setRealtime(realtime);
        });
        this.thing.setPropertyWriteHandler('endtime', async (endtime) => {
            await this.setEndtime(endtime);
        });
    }

    protected addActionHandlers(): void {
        this.thing.setActionHandler('run', async () => {
            await this.run();
        });
        this.thing.setActionHandler('stop', async () => {
            await this.stop();
        });
        this.thing.setActionHandler('setup', async () => {
            await this.setup();
        });
        this.thing.setActionHandler('clean', async () => {
            await this.clean();
        });
        this.thing.setActionHandler('postprocess', async () => {
            await this.postprocess();
        });
        this.thing.setActionHandler('addObject', async (props) => {
            await this.addObject(props);
        });
        this.thing.setActionHandler('removeObject', async (name) => {
            await this.removeObject(name);
        });
    }

    protected addEventHandlers(): void {
    }
}
