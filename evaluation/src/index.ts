import {Servient, Helpers} from '@node-wot/core';
import {HttpClientFactory} from '@node-wot/binding-http';
import dotenv from 'dotenv';
const fs = require('fs');

type PhyngsType = 'heaters' | 'acs' | 'windows' | 'doors' | 'all';
interface CsvData {
    caseName: string
    cores: number
    meshQuality: number
    type: PhyngsType
    phyngAmount: number
    elapsed: number
    error: string
}

dotenv.config();
const BASE_URL = process.env.HOST;
const MESH_STEP = Number(process.env.MESH_STEP);
const MAX_CORES = Number(process.env.MAX_CORES);
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

const CSV_COLUMN = 'Case Name;Cores;Mesh Quality;Phyngs Type;Phyngs Amount;Time, ms;Error\n';

let filePath = `./results/${new Date().toISOString()}.csv`;

fs.writeFile(filePath, CSV_COLUMN, function (err: any) {
    if (err) throw err;
});

let servient = new Servient();
servient.addClientFactory(new HttpClientFactory());

let wotClient: WoT.WoT;
let wotHelper = new Helpers(servient);

// Start servient
servient.start()
    .then((WoT) => {
        wotClient = WoT;
    })

function writeToCsv(data: CsvData) {
    let row = `${data.caseName};${data.cores};${data.meshQuality};${data.type};${data.phyngAmount};${data.elapsed}\n`;
    fs.appendFile(filePath, row, function (err: any) {
        if (err) throw err;
    })
}

async function addPhyng(caseThing: WoT.ConsumedThing, name: string,
                        location: Array<number>, data: any): Promise<WoT.ConsumedThing> {
    console.log(`Adding Phyng ${name} at the location ${location}`);
    data = {...data, 'title': name, 'location': location};
    await caseThing.invokeAction('addPhyng', data);
    let caseName = caseThing.getThingDescription().title;
    let td = await wotHelper.fetch(`${BASE_URL}/${caseName}-${name}/`);
    return wotClient.consume(td);
}

async function setPhyng(phyng: WoT.ConsumedThing, type: PhyngsType) {
    switch (type) {
        case "heaters":
            await phyng.writeProperty('temperature', '350');
            break;
        case "acs":
            await phyng.writeProperty('temperature', '283.15');
            await phyng.writeProperty('velocity', '5');
            await phyng.invokeAction('turnOn');
            break;
        case "windows":
            await phyng.writeProperty('temperature', '303.15');
            await phyng.writeProperty('velocity', '[-5, 0, 0]');
            await phyng.invokeAction('open');
            break;
        case "doors":
            await phyng.writeProperty('temperature', '296.15');
            await phyng.writeProperty('velocity', '[5, 0, 0]');
            await phyng.invokeAction('open');
            break;
    }
}

async function addCase(simulatorThing: WoT.ConsumedThing, caseName: string,
                       meshQuality: number, cores: number): Promise<WoT.ConsumedThing> {
    let parallel = cores > 1;
    let data = {...CASE_DATA, 'title': caseName, 'meshQuality': meshQuality, parallel};
    await simulatorThing.invokeAction('createCase', data);
    let caseTd = await wotHelper.fetch(`${BASE_URL}/${caseName}/`);
    return wotClient.consume(caseTd);
}

async function solveCase(caseThing: WoT.ConsumedThing,
                         meshQuality: number, cores: number,
                         type: PhyngsType, phyngAmount: number) {
    console.log(`Setting up the case with ${meshQuality} mesh, ${cores} cores`);
    let error = '';
    let elapsed: number = 0;
    try {
        let result = await caseThing.invokeAction('setup');
        if (result) {
            console.log(result);
            error = result;
        }
        let start = process.hrtime();
        result = await caseThing.invokeAction('run');
        elapsed = process.hrtime(start)[1] / 1000000;
        if (result) {
            console.log(result);
            error = result;
        }
    }
    catch (e: any) {
        error = e;
    }
    let data: CsvData = {
        caseName: caseThing.getThingDescription().title,
        cores,
        meshQuality,
        type,
        phyngAmount,
        elapsed,
        error
    }
    writeToCsv(data);
}

function getMaxPhyngs(data: any) {
    return WALLS_DATA.phyProperties.dimensions[1] / (data.phyProperties.dimensions[1] +
        data.phyProperties.location[1]);
}

async function phyngEvaluation(simulator: WoT.ConsumedThing,
                               meshQuality: number, cores: number,
                               type: PhyngsType, data: any,
                               caseThing: any = undefined, solve: boolean = true) {
    let numOfPhyngs = getMaxPhyngs(data) + 1;
    for (let phyngIter = 0; phyngIter < numOfPhyngs; phyngIter++) {
        if (!caseThing) {
            let caseName = `evalmesh${meshQuality}cores${cores}phyngs${type}${phyngIter}`
            caseThing = await addCase(simulator, caseName, meshQuality, cores);
            await addPhyng(caseThing, `walls`, WALLS_DATA.phyProperties.location, WALLS_DATA);
            await addPhyng(caseThing, `heater`, HEATER_DATA.phyProperties.location, HEATER_DATA);
        }
        for (let phyngNum = 0; phyngNum < (phyngIter + 1); phyngNum++) {
            let location = data.phyProperties.location;
            location[1] += phyngNum * (data.phyProperties.dimensions[1] + data.phyProperties.location[1]);
            let phyng = await addPhyng(caseThing, `${type}${phyngNum}`, location, data);
            await setPhyng(phyng, type);
        }
        if (solve) {
            await solveCase(caseThing, meshQuality, cores, type, numOfPhyngs);
        }
    }
}

async function evaluateCases(simulator: WoT.ConsumedThing, meshStep: number,
                             maxCores: number, heaters: boolean, acs: boolean,
                             windows: boolean, doors: boolean) {
    if (!(heaters || acs || windows || doors)) throw Error('Specify at least one evaluation Phyng');
    let maxMeshIter = 100 / meshStep + 1;
    maxCores /= 2 + 1;
    for (let meshIter = 0; meshIter < maxMeshIter; meshIter++) {
        let meshQuality = meshStep * meshIter;
        for (let coreIter = 0; coreIter < maxCores; coreIter++) {
            let cores = (2 * coreIter) || 1;
            // First - evaluate individual Phyng types
            if (heaters) {
                console.log(`Evaluating heaters with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'heaters', HEATER_DATA);
            }
            if (acs) {
                console.log(`Evaluating acs with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'acs', AC_DATA);
            }
            if (windows) {
                console.log(`Evaluating windows with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'windows', WINDOW_DATA);
            }
            if (doors) {
                console.log(`Evaluating doors with ${meshQuality} mesh, ${cores} cores`);
                await phyngEvaluation(simulator, meshQuality, cores, 'doors', DOOR_DATA);
            }

            // Evaluate all phyngs at once
            let caseName = `evalmesh${meshQuality}cores${cores}phyngsall`
            let caseThing = await addCase(simulator, caseName, meshQuality, cores);
            await addPhyng(caseThing, `walls`, WALLS_DATA.phyProperties.location, WALLS_DATA);
            let maxPhyngs = 0;
            console.log(`Evaluating all phyngs with ${meshQuality} mesh, ${cores} cores`);
            if (heaters) {
                await phyngEvaluation(simulator, meshQuality, cores, 'heaters', HEATER_DATA, caseThing, false);
                maxPhyngs += getMaxPhyngs(HEATER_DATA);
            }
            if (acs) {
                await phyngEvaluation(simulator, meshQuality, cores, 'acs', AC_DATA, caseThing, false);
                maxPhyngs += getMaxPhyngs(AC_DATA);
            }
            if (windows) {
                await phyngEvaluation(simulator, meshQuality, cores, 'windows', WINDOW_DATA, caseThing, false);
                maxPhyngs += getMaxPhyngs(WINDOW_DATA);
            }
            if (doors) {
                await phyngEvaluation(simulator, meshQuality, cores, 'doors', DOOR_DATA, caseThing, false);
                maxPhyngs += getMaxPhyngs(DOOR_DATA);
            }
            await solveCase(caseThing, meshQuality, cores, "all", maxPhyngs);
        }
    }
}

async function main() {
    let simulatorTd = await wotHelper.fetch(SIMULATOR_URL);
    let simulator = await wotClient.consume(simulatorTd);
    await evaluateCases(
        simulator,
        MESH_STEP,
        MAX_CORES,
        HEATERS,
        ACS,
        WINDOWS,
        DOORS
    );
}

(async () => {
    await main();
})().catch(e => {
    console.error(e);
})
