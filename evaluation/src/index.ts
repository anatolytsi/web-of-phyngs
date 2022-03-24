import {Servient, Helpers} from '@node-wot/core';
import {HttpClientFactory} from '@node-wot/binding-http';
import dotenv from 'dotenv';
import {NamedHrefs} from './interfaces';

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
const START_MESH = parseInt(process.env.START_MESH || "", 10) || MESH_STEP;
const MAX_MESH = parseInt(process.env.MAX_MESH || "", 10) || 100;
const MAX_CORES = parseInt(process.env.MAX_CORES || "", 10) || 8;
const CORES_STEP = parseInt(process.env.CORES_STEP || "", 10) || 2;
const START_CORES = parseInt(process.env.START_CORES || "", 10) || 0;
const HEATERS = parseInt(process.env.HEATERS || "", 10) || 0;
const HEATERS_STEP = parseInt(process.env.HEATERS_STEP || "", 10) || 1;
const ACS = parseInt(process.env.ACS || "", 10) || 0;
const ACS_STEP = parseInt(process.env.ACS_STEP || "", 10) || 1;
const WINDOWS = parseInt(process.env.WINDOWS || "", 10) || 0;
const WINDOWS_STEP = parseInt(process.env.WINDOWS_STEP || "", 10) || 1;
const DOORS = parseInt(process.env.DOORS || "", 10) || 0;
const DOORS_STEP = parseInt(process.env.DOORS_STEP || "", 10) || 1;
const TAKE_MOST = process.env.TAKE_MOST === '1';
const TAKE_LEAST = process.env.TAKE_LEAST === '1';
const SERVER_NAME = process.env.SERVER_NAME;
const FILENAME = process.env.FILENAME;

console.log(`Simulating for ${NUM_OF_TIMES}, Mesh step ${MESH_STEP}, cores ${MAX_CORES} with step ${CORES_STEP}`);

const SIMULATOR_URL = `${BASE_URL}/wopsimulator/`;
const CASE_DATA = require('../data/case.json');
const WALLS_DATA = require('../data/walls.json');
const AC_DATA = require('../data/ac.json');
const HEATER_DATA = require('../data/heater.json');
const WINDOW_DATA = require('../data/window.json');
const DOOR_DATA = require('../data/door.json');

const CSV_COLUMN = 'Case Name;Cores;Mesh Quality;Phyngs Type;Phyngs Amount;Setup Time, ms;Solving Time, ms;Error\n';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let dirPath = `./results/${SERVER_NAME ? SERVER_NAME + '/' : ''}`;

if (!fs.existsSync(dirPath)){
    fs.mkdirSync(dirPath);
}

let filePath = `${dirPath}${new Date().toISOString()}.csv`;

if (FILENAME) {
    filePath = `${dirPath}${FILENAME}.csv`
}

fs.writeFile(filePath, CSV_COLUMN, function (err: any) {
    if (err) throw err;
});

let servient = new Servient();
servient.addClientFactory(new HttpClientFactory());

let wotClient: WoT.WoT;
let wotHelper = new Helpers(servient);

let meshPhyngsLimit: any = {
    'heaters': {},
    'acs': {},
    'windows': {},
    'doors': {},
    'all': {}
}

function writeToCsv(data: CsvData) {
    let row = `${data.caseName};${data.cores};${data.meshQuality};${data.type};${data.phyngAmount};${data.elapsedSetup};${data.elapsedSolve};${data.error}\n`;
    fs.appendFile(filePath, row, function (err: any) {
        if (err) throw err;
    })
}

async function addPhyng(caseThing: WoT.ConsumedThing, name: string,
                        location: Array<number>, data: any): Promise<WoT.ConsumedThing> {
    console.log(`Adding Phyng ${name} at the location ${location}`);
    data = {...data, 'title': name};
    let phyProps: any = {};
    for (const key in data.phyProperties) {
        phyProps[key] = data.phyProperties[key];
    }
    location[0] = Math.round(location[0] * 100) / 100;
    phyProps.location = location;
    if ('locationIn' in data.phyProperties) {
        let increase = location[0] - data.phyProperties.location[0];
        let locationIn = [...data.phyProperties.locationIn];
        let locationOut = [...data.phyProperties.locationOut];
        locationIn[0] = Math.round((locationIn[0] + increase) * 100) / 100;
        locationOut[0] = Math.round((locationOut[0] + increase) * 100) / 100;
        phyProps.locationIn = locationIn;
        phyProps.locationOut = locationOut;
    }
    data.phyProperties = phyProps;
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
    data.sysProperties = {...CASE_DATA.sysProperties, meshQuality, parallel, cores};
    await simulatorThing.invokeAction('createCase', data);
    let caseTd = await wotHelper.fetch(`${BASE_URL}/${caseName}/`);
    return wotClient.consume(caseTd);
}

async function setupCase(caseThing: WoT.ConsumedThing, numOfRetries: number = 0,
                         retried: boolean = false): Promise<[number, any]> {
    try {
        if (retried) {
            await caseThing.invokeAction('clean');
            await delay(100);
        }
        let error = '';
        let start = Date.now();
        let result = await caseThing.invokeAction('setup');
        if (result && result.data) {
            console.log(result.data);
            if (numOfRetries) {
                await delay(500);
                return setupCase(caseThing, numOfRetries - 1, true)
            }
            error = `Setup: ${result.data}`;
            return [0, error];
        }
        return [Date.now() - start, error];
    } catch (e: any) {
        if (numOfRetries) {
            await delay(500);
                console.log(`Retrying to setup the case ${caseThing.getThingDescription().title}`);
            return setupCase(caseThing, numOfRetries - 1, true)
        }
        let error = `Setup: ${e}`;
        return [0, error];
    }
}

async function solveCase(caseThing: WoT.ConsumedThing): Promise<[number, any]> {
    try {
        let error = '';
        let start = Date.now();
        let result = await caseThing.invokeAction('run');
        let elapsedSolve = Date.now() - start;
        if (result && result.data) {
            console.log(result.data);
            error = `Solver: ${result.data}`;
            return [0, error];
        }
        return [elapsedSolve, error];
    } catch (e) {
        console.error(e);
        let error = `Solver: ${e}`;
        return [0, error];
    }
}

function getMaxPhyngs(data: any, type: PhyngsType) {
    let maxPhyngs = Math.round(WALLS_DATA.phyProperties.dimensions[0] / (data.phyProperties.dimensions[0] +
        data.phyProperties.location[0]));
    switch (type) {
        case "heaters": return HEATERS <= maxPhyngs ? HEATERS : maxPhyngs;
        case "acs": return ACS <= maxPhyngs ? ACS : maxPhyngs;
        case "windows": return WINDOWS <= maxPhyngs ? WINDOWS : maxPhyngs;
        case "doors": return DOORS <= maxPhyngs ? DOORS : maxPhyngs;
    }
    return 0;
}

function getPhyngStep(type: PhyngsType) {
    switch (type) {
        case "heaters": return HEATERS_STEP;
        case "acs": return ACS_STEP;
        case "windows": return WINDOWS_STEP;
        case "doors": return DOORS_STEP;
    }
    return 0;
}

async function phyngEvaluation(simulator: WoT.ConsumedThing,
                               meshQuality: number, cores: number,
                               type: PhyngsType, data: any,
                               caseThing: any = undefined, solve: boolean = true,
                               numOfRetries: number = 2, curPhyng: number = 0,
                               origNumOfRetries: number = 2) {
    let elapsedSetup, elapsedSolve = 0;
    let errorSetup, errorSolve = '';
    let caseProvided = !!caseThing;
    let caseName = '';
    let phyngStep = getPhyngStep(type);
    let numOfPhyngs = Math.floor((TAKE_LEAST ? 1 : getMaxPhyngs(data, type)) / phyngStep);

    curPhyng = TAKE_MOST ? numOfPhyngs - 1 : curPhyng;
    for (let phyngIter = curPhyng; phyngIter < numOfPhyngs; phyngIter++) {
        let phyngAmount = phyngStep === 1 ? (phyngIter + 1) : ((phyngIter * phyngStep) || 1);

        // Do not evaluate any phyngs further
        if (meshQuality in meshPhyngsLimit[type] && phyngAmount >= meshPhyngsLimit[type][meshQuality]) {
            return
        }

        if (!caseThing) {
            caseName = `m${meshQuality}c${cores}ph${type[0]}${phyngAmount}`
            caseThing = await addCase(simulator, caseName, meshQuality, cores);
            await delay(500);
            await addPhyng(caseThing, `walls`, WALLS_DATA.phyProperties.location, {...WALLS_DATA});
            await delay(100);
            if (type !== 'heaters') {
                await addPhyng(caseThing, `heater`, HEATER_DATA.phyProperties.location, {...HEATER_DATA});
                await delay(100);
                if (type === 'doors') {
                    let window = await addPhyng(caseThing, `window`, WINDOW_DATA.phyProperties.location,
                        {...WINDOW_DATA});
                    await window.writeProperty('temperature', 303.15);
                    await delay(100);
                    await window.writeProperty('velocity', [-5, 0, 0]);
                    await delay(100);
                    await window.invokeAction('open');
                    await delay(100);
                }
            }
        }
        let phyngs: Array<WoT.ConsumedThing> = [];
        for (let phyngNum = 0; phyngNum < phyngAmount; phyngNum++) {
            let location = [...data.phyProperties.location];
            location[0] += phyngNum * (data.phyProperties.dimensions[0] + data.phyProperties.location[0]);
            phyngs.push(await addPhyng(caseThing, `${type}${phyngNum + 1}`, location, data));
            await delay(100);
        }
        let error = '';
        [elapsedSetup, errorSetup] = await setupCase(caseThing, 2);
        if (errorSetup) {
            error = errorSetup;
        }
        await delay(100);

        for (let phyngNum = 0; phyngNum < phyngAmount; phyngNum++) {
            try {
                await setPhyng(phyngs[phyngNum], type);
            } catch (e) {
                error = 'Some surface was not produced'
            }
            await delay(100);
        }

        if (solve) {
            if (!error) {
                [elapsedSolve, errorSolve] = await solveCase(caseThing);
                if (errorSolve) {
                    error = errorSolve;
                }
            }
            await simulator.invokeAction('deleteCase', caseName);
            if (error && !caseProvided && numOfRetries) {
                await delay(100);
                await phyngEvaluation(simulator, meshQuality, cores, type, data,
                    undefined, true, numOfRetries - 1, phyngIter - 1, numOfRetries);
                return
            }
            let csvData: CsvData = {
                caseName: caseThing.getThingDescription().title,
                cores,
                meshQuality,
                type,
                phyngAmount,
                elapsedSetup,
                elapsedSolve,
                error
            }
            writeToCsv(csvData);
            await delay(5000);
            caseThing = undefined;
            numOfRetries = origNumOfRetries;

            if (elapsedSolve > 60000) {
                meshPhyngsLimit[type][meshQuality] = phyngAmount;
                return;
            }
        }
    }
}

async function evaluateCases(simulator: WoT.ConsumedThing,
                             meshStep: number, startMesh: number,
                             maxCores: number, coresStep: number, startCores: number,
                             heaters: number, acs: number,
                             windows: number, doors: number) {
    if (!(heaters || acs || windows || doors)) throw Error('Specify at least one evaluation Phyng');
    let remainder = startMesh % meshStep;
    let startIter = Math.floor(startMesh / meshStep);
    let maxMeshIter = MAX_MESH / meshStep + 1;
    let curMaxCores = maxCores / coresStep + 1;
    for (let meshIter = startMesh / meshStep; meshIter < maxMeshIter; meshIter++) {
        let meshQuality = (meshIter === startIter && remainder) ? startMesh : meshIter * meshStep;
        for (let coreIter = startCores / coresStep; coreIter < curMaxCores; coreIter++) {
            let cores = (coresStep * coreIter) || 1;
            // First - evaluate individual Phyng types
            if (heaters) {
                console.log(`Evaluating ${heaters} heaters with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'heaters', {...HEATER_DATA});
            }
            if (acs) {
                console.log(`Evaluating ${acs} acs with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'acs', {...AC_DATA});
            }
            if (windows) {
                console.log(`Evaluating ${windows} windows with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'windows', {...WINDOW_DATA});
            }
            if (doors) {
                console.log(`Evaluating ${doors} doors with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'doors', {...DOOR_DATA});
            }
        }
    }
}

async function main() {
    let simulatorTd = await wotHelper.fetch(SIMULATOR_URL);
    let simulator = await wotClient.consume(simulatorTd);
    let usedCases: Array<NamedHrefs> = await simulator.readProperty('cases');
    for (let i = 0; i < NUM_OF_TIMES; i++) {
        for (const simCase of usedCases) {
            await simulator.invokeAction('deleteCase', simCase.name);
        }
        await evaluateCases(
            simulator,
            MESH_STEP,
            START_MESH,
            MAX_CORES,
            CORES_STEP,
            START_CORES,
            HEATERS,
            ACS,
            WINDOWS,
            DOORS
        );
    }
}

(async () => {
    // Start servient
    servient.start()
        .then(async (WoT) => {
            wotClient = WoT;
            await main();
        })
})().catch(e => {
    console.error(e);
})
