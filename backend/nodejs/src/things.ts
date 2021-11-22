import axios from "axios";

export abstract class AbstractThing {
    protected wot: WoT.WoT;
    protected thing!: WoT.ExposedThing;
    protected host: string;
    public base: string;
    public ready: boolean = false;

    protected abstract addPropertyHandlers(): void;

    protected abstract addActionHandlers(): void;

    protected abstract addEventHandlers(): void;

    constructor(host: string, wot: WoT.WoT, td: any) {
        this.wot = wot;
        this.host = host;
        this.base = host;
        this.createFromTd(td)
            .then(() => {
                this.ready = true;
            });
    }

    protected async createFromTd(td: any) {
        this.thing = await this.wot.produce(td)
        await this.thing.expose();
        this.addPropertyHandlers();
        this.addActionHandlers();
        this.addEventHandlers();
    }

    public async destroy() {
        await this.thing.destroy();
        // TODO: delete something else?
    }
}

interface ObjectPropsBase {
    name: string;
    type: string;
    location?: Array<number>;
}

interface ActuatorProps extends ObjectPropsBase {
    rotation?: Array<number>;
}

export interface ActuatorPropsCreated extends ActuatorProps {
    dimensions: Array<number>;
}

export interface ActuatorPropsTemplate extends ActuatorProps {
    template: string;
}

export interface SensorProps extends ObjectPropsBase {
    field: string;
}

export abstract class AbstractObject extends AbstractThing {
    protected caseName: string;
    public name: string;

    constructor(host: string, wot: WoT.WoT, td: any, caseName: string, name: string) {
        super(host, wot, td);
        this.caseName = caseName;
        this.name = name;
        this.base = `${this.host}/case/${this.caseName}/object/${this.name}`;
    }

    public createObject(props: ActuatorPropsCreated | ActuatorPropsTemplate | SensorProps) {
        let data = {...props};
        // @ts-ignore
        delete data.name;
        axios.post(this.base, data); // Add object to simulator
    }
}

export abstract class AbstractCase extends AbstractThing {
    protected name: string;
    protected objects: { [key: string]: AbstractObject };
    protected _meshQuality = 50;
    protected _cleanLimit = 0;
    protected _parallel = true;
    protected _cores = 4;

    protected abstract addObjectToDict(props: ActuatorPropsCreated | ActuatorPropsTemplate | SensorProps): void;

    constructor(host: string, wot: WoT.WoT, td: any, name: string) {
        super(host, wot, td);
        this.name = name;
        this.base = `${this.host}/case/${this.name}`;
        this._meshQuality = 50;
        this._cleanLimit = 0;
        this._parallel = true;
        this._cores = 4;
        this.objects = {};
        this.getParams();
        this.getObjects();
    }

    public async addObject(props: ActuatorPropsCreated | ActuatorPropsTemplate | SensorProps) {
        this.addObjectToDict(props);
        await axios.post(this.base, props);
    };

    public async removeObject(name: string) {
        if (name in this.objects) {
            await this.objects[name].destroy();
            delete this.objects[name];
        }
    }

    public async getParams() {
        let response = await axios.get(`${this.base}`);
        let caseParams = response.data;
        this._meshQuality = caseParams.mesh_quality;
        this._cleanLimit = caseParams.clean_limit;
        this._parallel = caseParams.parallel;
        this._cores = caseParams.cores;
    }

    public async getObjects() {
        let response = await axios.get(`${this.base}/object`);
        return response.data;
    }

    public get meshQuality() {
        return this._meshQuality;
    }

    public get cleanLimit() {
        return this._cleanLimit;
    }

    public get parallel() {
        return this._parallel;
    }

    public get cores() {
        return this._cores;
    }

    public async setMeshQuality(meshQuality: number) {
        this._meshQuality = meshQuality;
        await axios.patch(this.base, {mesh_quality: meshQuality});
    }

    public async setCleanLimit(cleanLimit: number) {
        this._cleanLimit = cleanLimit;
        await axios.patch(this.base, {clean_limit: cleanLimit});
    }

    public async setParallel(parallel: boolean) {
        this._parallel = parallel;
        await axios.patch(this.base, {parallel: parallel});
    }

    public async setCores(cores: number) {
        this._cores = cores;
        await axios.patch(this.base, {cores: cores});
    }

    protected getObjectByName(name: string) {
        if (name in this.objects) {
            return this.objects[name];
        }
        return undefined;
    }

    protected addPropertyHandlers() {
        this.thing.setPropertyReadHandler('meshQuality', async () => this.meshQuality);
        this.thing.setPropertyReadHandler('cleanLimit', async () => this.cleanLimit);
        this.thing.setPropertyReadHandler('parallel', async () => this.parallel);
        this.thing.setPropertyReadHandler('cores', async () => this.cores);
        this.thing.setPropertyReadHandler('objects', async () => {
            let objects: Array<string> = [];
            for (const name in this.objects) {
                objects.push(this.objects[name].base);
            }
            return objects;
        });
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

    protected addActionHandlers() {
    }

    protected addEventHandlers() {
    }
}

export class Simulator extends AbstractThing {
    protected cases: { [key: string]: AbstractCase };
    protected caseTypes: { [key: string]: { [key: string]: Function} | { [key: string]: any} };

    constructor(host: string, wot: WoT.WoT, td: any, caseTypes: any) {
        super(host, wot, td);
        this.cases = {};
        this.base = `${this.host}/case`
        this.caseTypes = caseTypes;
        this.getCases()
    }

    protected addCaseToDict(type: string, name: string): AbstractCase {
        // TODO: caseParam with constructor and TD in it
        let caseParam = this.caseTypes[type];
        caseParam.td.title = name;
        return caseParam.constructor(this.host, this.wot, caseParam.td, name);
    };

    public getCases() {
        return new Promise(async (resolve) => {
            let response = await axios.get(`${this.base}`);
            let cases: Array<string> = response.data;
            for (const name of cases) {
                let normalName = `${name.replace('.case', '')}`;
                let response = await axios.get(`${this.base}/${normalName}`);
                this.cases[normalName] = this.addCaseToDict(response.data.type, normalName);
            }
            resolve(cases);
        })
    }

    public createCase(name: string) {
        return axios.post(`${this.base}/${name}`);
    }

    public deleteCase(name: string) {
        return axios.delete(`${this.base}/${name}`);
    }

    protected addPropertyHandlers() {
        this.thing.setPropertyReadHandler('cases', async () => {
            return await this.getCases();
        });
    }

    protected addActionHandlers() {
        this.thing.setActionHandler('createCase', async (name) => {
            await this.createCase(name);
            // TODO: instantiate the case class here and return a TD
        });
        this.thing.setActionHandler('deleteCase', async (name) => {
            await this.deleteCase(name);
            // TODO: delete case instance here
        });
    }

    protected addEventHandlers() {
    }
}
