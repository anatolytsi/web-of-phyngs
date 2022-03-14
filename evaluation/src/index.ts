import {Servient, Helpers} from '@node-wot/core';
import {HttpClientFactory} from '@node-wot/binding-http';
import dotenv from 'dotenv';

const path = require('path');
const fs = require('fs');

type PhyngsType = 'heaters' | 'acs' | 'windows' | 'doors' | 'all';

interface CsvData {
    caseName: string
    cores: number
    meshQuality: number
    type: PhyngsType
    phyngAmount: number
    elapsedSetup: number
    elapsedSolve: number
    error: string
}

dotenv.config({path: path.resolve(__dirname, '../.env')});
const BASE_URL = process.env.HOST;
const NUM_OF_TIMES = parseInt(process.env.NUM_OF_TIMES || "", 10) || 100;
const MESH_STEP = parseInt(process.env.MESH_STEP || "", 10) || 10;
const MAX_CORES = parseInt(process.env.MAX_CORES || "", 10) || 8;
const CORES_STEP = parseInt(process.env.CORES_STEP || "", 10) || 2;
const HEATERS = process.env.HEATERS === '1';
const ACS = process.env.ACS === '1';
const WINDOWS = process.env.WINDOWS === '1';
const DOORS = process.env.DOORS === '1';

const SIMULATOR_URL = `${BASE_URL}/wopsimulator/`;
const CASE_DATA = require('../data/case.json');
const WALLS_DATA = require('../data/walls.json');
const AC_DATA = require('../data/ac.json');
const HEATER_DATA = require('../data/heater.json');
const WINDOW_DATA = require('../data/window.json');
const DOOR_DATA = require('../data/door.json');

const CSV_COLUMN = 'Case Name;Cores;Mesh Quality;Phyngs Type;Phyngs Amount;Setup Time, ms;Solving Time, ms;Error\n';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let filePath = `./results/${new Date().toISOString()}.csv`;

fs.writeFile(filePath, CSV_COLUMN, function (err: any) {
    if (err) throw err;
});

let servient = new Servient();
servient.addClientFactory(new HttpClientFactory());

let wotClient: WoT.WoT;
let wotHelper = new Helpers(servient);

let usedCases: Array<string> = [];

// Start servient
servient.start()
    .then((WoT) => {
        wotClient = WoT;
    })

function writeToCsv(data: CsvData) {
    let row = `${data.caseName};${data.cores};${data.meshQuality};${data.type};${data.phyngAmount};${data.elapsedSetup};${data.elapsedSolve}${data.error}\n`;
    fs.appendFile(filePath, row, function (err: any) {
        if (err) throw err;
    })
}

async function addPhyng(caseThing: WoT.ConsumedThing, name: string,
                        location: Array<number>, data: any): Promise<WoT.ConsumedThing> {
    console.log(`Adding Phyng ${name} at the location ${location}`);
    data = {...data, 'title': name};
    data.phyProperties = {...data.phyProperties, location};
    await caseThing.invokeAction('addPhyng', data);
    let caseName = caseThing.getThingDescription().title;
    let td = await wotHelper.fetch(`${BASE_URL}/${caseName}-${name}/`);
    return wotClient.consume(td);
}

async function setPhyng(phyng: WoT.ConsumedThing, type: PhyngsType) {
    switch (type) {
        case "heaters":
            await phyng.writeProperty('temperature', 350);
            break;
        case "acs":
            await phyng.writeProperty('temperature', 283.15);
            await phyng.writeProperty('velocity', 5);
            await phyng.invokeAction('turnOn');
            break;
        case "windows":
            await phyng.writeProperty('temperature', 303.15);
            await phyng.writeProperty('velocity', [-5, 0, 0]);
            await phyng.invokeAction('open');
            break;
        case "doors":
            await phyng.writeProperty('temperature', 296.15);
            await phyng.writeProperty('velocity', [5, 0, 0]);
            await phyng.invokeAction('open');
            break;
    }
}

async function addCase(simulatorThing: WoT.ConsumedThing, caseName: string,
                       meshQuality: number, cores: number): Promise<WoT.ConsumedThing> {
    let parallel = cores > 1;
    let data = {...CASE_DATA, 'title': caseName};
    data.sysProperties = {...CASE_DATA.sysProperties, meshQuality, parallel};
    await simulatorThing.invokeAction('createCase', data);
    let caseTd = await wotHelper.fetch(`${BASE_URL}/${caseName}/`);
    return wotClient.consume(caseTd);
}

async function setupCase(caseThing: WoT.ConsumedThing, numOfRetries: number = 0,
                         retried: boolean = false): Promise<[number, any]> {
    try {
        if (retried) {
            await caseThing.invokeAction('clean');
            await delay(1000);
        }
        let error = '';
        let start = Date.now();
        let result = await caseThing.invokeAction('setup');
        if (result) {
            console.log(result);
            error = result;
        }
        return [Date.now() - start, error];
    } catch (e: any) {
        if (numOfRetries) {
            await delay(1000);
            return setupCase(caseThing, numOfRetries - 1, true)
        }
        throw Error(e);
    }
}

async function solveCase(caseThing: WoT.ConsumedThing): Promise<[number, any]> {
    let error = '';
    let start = Date.now();
    let result = await caseThing.invokeAction('run');
    let elapsedSolve = Date.now() - start;
    if (result) {
        console.log(result);
        error = result;
    }
    return [elapsedSolve, error];
}

async function runCase(caseThing: WoT.ConsumedThing,
                       meshQuality: number, cores: number,
                       type: PhyngsType, phyngAmount: number) {
    console.log(`Setting up the case with ${meshQuality} mesh, ${cores} cores`);
    let error, errorSetup, errorSolve = '';
    let elapsedSetup: number = 0;
    let elapsedSolve: number = 0;
    try {
        [elapsedSetup, errorSetup] = await setupCase(caseThing, 2);
        await delay(1000);
        [elapsedSolve, errorSolve] = await solveCase(caseThing);
        let errorPres = (elapsedSolve || errorSolve) !== '';
        error = `${errorSetup}${errorPres ? '\t' : ''}${errorSolve}`
        await caseThing.invokeAction('stop');
    } catch (e: any) {
        error = e;
    }
    let data: CsvData = {
        caseName: caseThing.getThingDescription().title,
        cores,
        meshQuality,
        type,
        phyngAmount,
        elapsedSetup,
        elapsedSolve,
        error
    }
    writeToCsv(data);
    await delay(5000);
}

function getMaxPhyngs(data: any) {
    return Math.round(WALLS_DATA.phyProperties.dimensions[0] / (data.phyProperties.dimensions[0] +
        data.phyProperties.location[0]));
}

async function phyngEvaluation(simulator: WoT.ConsumedThing,
                               meshQuality: number, cores: number,
                               type: PhyngsType, data: any,
                               caseThing: any = undefined, solve: boolean = true) {
    let numOfPhyngs = getMaxPhyngs(data) + 1;
    for (let phyngIter = 0; phyngIter < numOfPhyngs; phyngIter++) {
        if (!caseThing) {
            let caseName = `evalmesh${meshQuality}cores${cores}phyngs${type}${phyngIter + 1}`
            caseThing = await addCase(simulator, caseName, meshQuality, cores);
            await delay(500);
            await addPhyng(caseThing, `walls`, WALLS_DATA.phyProperties.location, {...WALLS_DATA});
            await delay(100);
            if (type !== 'heaters') {
                await addPhyng(caseThing, `heater`, HEATER_DATA.phyProperties.location, {...HEATER_DATA});
            await delay(100);
            }
        }
        for (let phyngNum = 0; phyngNum < (phyngIter + 1); phyngNum++) {
            let location = [...data.phyProperties.location];
            location[0] += phyngNum * (data.phyProperties.dimensions[0] + data.phyProperties.location[0]);
            let phyng = await addPhyng(caseThing, `${type}${phyngNum + 1}`, location, data);
            await delay(100);
            await setPhyng(phyng, type);
            await delay(100);
        }
        if (solve) {
            await runCase(caseThing, meshQuality, cores, type, phyngIter + 1);
            caseThing = undefined;
        }
    }
}

async function evaluateCases(simulator: WoT.ConsumedThing, meshStep: number,
                             maxCores: number, coresStep: number,
                             heaters: boolean, acs: boolean,
                             windows: boolean, doors: boolean) {
    if (!(heaters || acs || windows || doors)) throw Error('Specify at least one evaluation Phyng');
    let maxMeshIter = 100 / meshStep + 1;
    maxCores /= coresStep + 1;
    for (let meshIter = 1; meshIter < maxMeshIter; meshIter++) {
        let meshQuality = meshStep * meshIter;
        for (let coreIter = 0; coreIter < maxCores; coreIter++) {
            let cores = (coresStep * coreIter) || 1;
            // First - evaluate individual Phyng types
            if (heaters) {
                console.log(`Evaluating heaters with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'heaters', {...HEATER_DATA});
            }
            if (acs) {
                console.log(`Evaluating acs with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'acs', {...AC_DATA});
            }
            if (windows) {
                console.log(`Evaluating windows with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'windows', {...WINDOW_DATA});
            }
            if (doors) {
                console.log(`Evaluating doors with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'doors', {...DOOR_DATA});
            }

            // Evaluate all phyngs at once
            let caseName = `evalmesh${meshQuality}cores${cores}phyngsall`
            let caseThing = await addCase(simulator, caseName, meshQuality, cores);
            await addPhyng(caseThing, `walls`, WALLS_DATA.phyProperties.location, WALLS_DATA);
            let maxPhyngs = 0;
            console.log(`Evaluating all phyngs with ${meshQuality} mesh, ${cores} cores`);
            if (heaters) {
                await phyngEvaluation(simulator, meshQuality, cores, 'heaters', {...HEATER_DATA},
                    caseThing, false);
                maxPhyngs += getMaxPhyngs(HEATER_DATA);
            }
            if (acs) {
                await phyngEvaluation(simulator, meshQuality, cores, 'acs', {...AC_DATA},
                    caseThing, false);
                maxPhyngs += getMaxPhyngs(AC_DATA);
            }
            if (windows) {
                await phyngEvaluation(simulator, meshQuality, cores, 'windows', {...WINDOW_DATA},
                    caseThing, false);
                maxPhyngs += getMaxPhyngs(WINDOW_DATA);
            }
            if (doors) {
                await phyngEvaluation(simulator, meshQuality, cores, 'doors', {...DOOR_DATA},
                    caseThing, false);
                maxPhyngs += getMaxPhyngs(DOOR_DATA);
            }
            await runCase(caseThing, meshQuality, cores, "all", maxPhyngs);
        }
    }
}

async function main() {
    let simulatorTd = await wotHelper.fetch(SIMULATOR_URL);
    let simulator = await wotClient.consume(simulatorTd);
    for (let i = 0; i < NUM_OF_TIMES; i++) {
        for (const simCase of usedCases) {
            await simulator.invokeAction('deleteCase', simCase);
        }
        await evaluateCases(
            simulator,
            MESH_STEP,
            MAX_CORES,
            CORES_STEP,
            HEATERS,
            ACS,
            WINDOWS,
            DOORS
        );
    }
}

(async () => {
    await main();
})().catch(e => {
    console.error(e);
})
