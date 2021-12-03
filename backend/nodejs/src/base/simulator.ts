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
import {CaseParameters} from './interfaces';
import {AnyUri} from 'wot-thing-description-types';
import {responseIsUnsuccessful, responseIsSuccessful} from "./helpers";

/**
 * Case Hyperlink REFerences (HREFs).
 */
interface CaseHrefs {
    /** Case name. */
    name: string;
    /** Case HREFs. */
    hrefs: AnyUri[]
}

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
     * @protected
     * @async
     */
    protected async initCaseByName(name: string): Promise<void> {
        let response = await axios.get(`${this.couplingUrl}/${name}`);
        if (!(name in this.cases)) {
            this.cases[name] = this.constructExposedCase(response.data.type, name);
            await this.cases[name].ready;
            this.casesHrefs.push({name: name, hrefs: this.cases[name].getHrefs()});
        }
    }

    /**
     * Loads available cases from the simulator backend.
     * @return {Promise<boolean>} Cases loaded promise.
     * @protected
     */
    protected loadAvailableCases(): Promise<boolean> {
        return new Promise(async (resolve) => {
            let response = await axios.get(`${this.couplingUrl}`);
            let caseNames: Array<string> = response.data;
            this.casesHrefs = [];
            for (const name of caseNames) {
                let normalName = `${name.replace('.case', '')}`;
                await this.initCaseByName(normalName);
            }
            resolve(true);
        })
    }

    /**
     * Creates case with given parameters on the simulator backend.
     * @param {CaseParameters} params Case parameters.
     * @return {Promise<AxiosResponse>} Simulator backend response promise.
     */
    public createCase(params: CaseParameters): Promise<AxiosResponse> {
        let {name, ...data} = params;
        return axios.post(`${this.couplingUrl}/${name}`, data);
    }

    /**
     * Deletes case by its name.
     * @param {string} name Name of the case.
     * @return {Promise<AxiosResponse>} Simulator backend response promise.
     */
    public deleteCase(name: string): Promise<AxiosResponse> {
        if (name in this.cases) {
            let index = this.casesHrefs.findIndex(x => x.name === name);
            this.casesHrefs.splice(index, 1);
            this.cases[name].destroy();
            delete this.cases[name];
        }
        return axios.delete(`${this.couplingUrl}/${name}`);
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('cases', async () => {
            return this.casesHrefs;
        });
    }

    protected addActionHandlers(): void {
        this.thing.setActionHandler('createCase', async (params) => {
            await this.createCase(params);
            await this.initCaseByName(params.name);
        });
        this.thing.setActionHandler('deleteCase', async (name) => {
            await this.deleteCase(name);
        });
    }

    protected addEventHandlers(): void {
    }
}
