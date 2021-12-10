/**
 * Simulator module.
 *
 * @file   Contains a Simulator class that is used to wrap python simulations in node-wot interface along with helper interfaces.
 * @author Anatolii Tsirkunenko
 * @since  28.11.2021
 */
import axios, {AxiosResponse} from 'axios';
import {AbstractThing} from './thing';
import {AbstractCase} from './case';
import {CaseParameters, CaseHrefs, SimulationErrors} from './interfaces';
import {responseIsUnsuccessful, responseIsSuccessful} from "./helpers";

/**
 * Case type constructor function.
 */
interface CaseTypeConstructor {
    (host: string, wot: WoT.WoT, tm: WoT.ThingDescription, name: string): AbstractCase;
}

/**
 * Case type constructor parameters.
 */
interface CaseTypeConstructorParams {
    /** Case type constructor. */
    constructor: CaseTypeConstructor;
    /** Case type thing model. */
    tm: WoT.ThingDescription;
}

/**
 * Case type constructor with type name as key.
 */
export interface CaseConstructorType {
    [type: string]: CaseTypeConstructorParams;
}

/**
 * A simulator Thing. Provides a WoT wrapper to simulator backend.
 * @class Simulator
 */
export class Simulator extends AbstractThing {
    /** Cases used in a simulation. */
    protected cases: { [name: string]: AbstractCase };
    /** Array of cases used in a
     * simulation with their HREFs. */
    protected casesHrefs: CaseHrefs[];
    /** Case types constructors, used to
     * instantiate cases according to their type. */
    protected caseTypesConstructors: CaseConstructorType;

    constructor(host: string, wot: WoT.WoT, tm: WoT.ThingDescription, caseTypesConstructors: CaseConstructorType) {
        super(host, wot, tm);
        this.cases = {};
        this.casesHrefs = []
        this.couplingUrl = `${this.host}/case`
        this.caseTypesConstructors = caseTypesConstructors;
        this.loadAvailableCases()
    }

    /**
     * Constructs a case Thing according
     * to a type and assigns a name to it.
     * @param {string} type Type of a case.
     * @param {string} name Name of a new case.
     * @return {AbstractCase} A new case instance.
     * @protected
     */
    protected constructExposedCase(type: string, name: string): AbstractCase {
        let caseConstructorParams = this.caseTypesConstructors[type];
        caseConstructorParams.tm.title = name;
        return caseConstructorParams.constructor(this.host, this.wot, {...caseConstructorParams.tm}, name);
    };

    /**
     * Initializes a new case with a given name.
     * @param {string} name Name of a case to initialize.
     * @return {Promise<string | void>} Init error or nothing.
     * @protected
     * @async
     */
    protected async initCaseByName(name: string): Promise<string | void> {
        let response: AxiosResponse = await axios.get(`${this.couplingUrl}/${name}`);
        if (!(name in this.cases) && responseIsSuccessful(response.status)) {
            this.cases[name] = this.constructExposedCase(response.data.type, name);
            await this.cases[name].ready;
            this.casesHrefs.push({name, hrefs: this.cases[name].getHrefs()});
            return;
        }
        return response.data;
    }

    /**
     * Loads available cases from the simulator backend.
     * @return {Promise<string | void>} Load error or nothing.
     * @protected
     * @async
     */
    protected async loadAvailableCases(): Promise<string | void> {
        let response: AxiosResponse = await axios.get(`${this.couplingUrl}`);
        if (responseIsUnsuccessful(response.status)) {
            return response.data;
        }
        let caseNames: string[] = response.data;
        this.casesHrefs = [];
        for (const name of caseNames) {
            let normalName = `${name.replace('.case', '')}`;
            await this.initCaseByName(normalName);
        }
    }

    /**
     * Returns simulation errors object.
     * @return {Promise<SimulationErrors>} Simulator errors object.
     * @async
     */
    public async getErrors(): Promise<SimulationErrors> {
        let response: AxiosResponse = await axios.get(`${this.couplingUrl}/errors`);
        return response.data;
    }

    /**
     * Creates case with given parameters on the simulator backend.
     * @param {CaseParameters} params Case parameters.
     * @return {Promise<string>} Simulator backend response promise.
     * @async
     */
    public async createCase(params: CaseParameters): Promise<string> {
        let {name, ...data} = params;
        let response: AxiosResponse = await axios.post(`${this.couplingUrl}/${name}`, data);
        return response.data;
    }

    /**
     * Deletes case by its name.
     * @param {string} name Name of the case.
     * @return {Promise<string>} Simulator backend response promise.
     * @async
     */
    public async deleteCase(name: string): Promise<string> {
        if (name in this.cases) {
            let index = this.casesHrefs.findIndex(x => x.name === name);
            this.casesHrefs.splice(index, 1);
            await this.cases[name].destroy();
            delete this.cases[name];
        }
        let response: AxiosResponse = await axios.delete(`${this.couplingUrl}/${name}`);
        return response.data;
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('cases', async () => {
            return this.casesHrefs;
        });
        this.thing.setPropertyReadHandler('errors', async () => {
            return await this.getErrors();
        });
    }

    protected addActionHandlers(): void {
        this.thing.setActionHandler('createCase', async (params) => {
            await this.createCase(params);
            return await this.initCaseByName(params.name);
        });
        this.thing.setActionHandler('deleteCase', async (name) => {
            return await this.deleteCase(name);
        });
    }

    protected addEventHandlers(): void {
    }
}
