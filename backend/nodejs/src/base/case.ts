/**
 * Case module.
 *
 * @file   Contains an AbstractCase class that is used as a base for all case types.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import axios from 'axios';
import {AbstractThing} from './thing';
import {CaseParameters, ObjectProps} from './interfaces';
import {AbstractObject} from './object';

/** Case commands allowed in the simulator. */
type CaseCommand = 'run' | 'stop' | 'setup' | 'clean' | 'postprocess';

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
            await axios.patch(this.couplingUrl, {mesh_quality: meshQuality});
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
            await axios.patch(this.couplingUrl, {clean_limit: cleanLimit});
        } else {
            // TODO: error
            console.error('Cleaning limit cannot be negative!')
        }
    }

    /**
     * Gets case name.
     * @return {boolean} name of a case.
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
        await axios.patch(this.couplingUrl, {parallel: parallel});
    }

    /**
     * Gets case name.
     * @return {number} name of a case.
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
            await axios.patch(this.couplingUrl, {cores: cores});
        } else {
            console.log('Number of cores cannot be negative!')
        }
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
     * Updates case parameters from a simulation server.
     * @async
     */
    public async updateParams(): Promise<void> {
        let response = await axios.get(`${this.couplingUrl}`);
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
        let response = await axios.post(`${this.couplingUrl}/object/${name}`, data);
        if (response.status === 201) {
            this.addObjectToDict(props);
        } else {
            console.error(response.data);
        }
    }

    /**
     * Removes an object with a given name from a simulator.
     * @param {string} name Name of an object.
     */
    public async removeObject(name: string): Promise<void> {
        if (name in this.objects) {
            await this.objects[name].destroy();
            delete this.objects[name];
        }
    }

    /**
     * Gets case objects with their HREFs.
     * @return {string[][]} Objects with name and HREFs
     */
    public getObjects(): string[][] {
        if (this.objects) {
            let objects: string[][] = [];
            for (const name in this.objects) {
                objects.push(this.objects[name].getHrefs());
            }
            return objects;
        }
        return [];
    }

    /**
     * Gets objects from a simulation.
     * @return {Promise<any>} Simulation objects.
     * @async
     * @protected
     */
    protected async getObjectsFromSimulator(): Promise<any> {
        let response = await axios.get(`${this.couplingUrl}/object`);
        return response.data;
    }

    /**
     * Executes a case command.
     * @param {CaseCommand} command Case command to execute.
     * @async
     * @protected
     */
    protected async executeCmd(command: CaseCommand): Promise<void> {
        let response = await axios.post(`${this.couplingUrl}/${command}`);
        if (response.status !== 200) {
            console.error(response.data);
        }
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('meshQuality', async () => this.meshQuality);
        this.thing.setPropertyReadHandler('cleanLimit', async () => this.cleanLimit);
        this.thing.setPropertyReadHandler('parallel', async () => this.parallel);
        this.thing.setPropertyReadHandler('cores', async () => this.cores);
        this.thing.setPropertyReadHandler('objects', async () => this.getObjects());

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