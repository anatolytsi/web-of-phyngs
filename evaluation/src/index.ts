import {Servient, Helpers} from '@node-wot/core';
import {HttpClientFactory} from '@node-wot/binding-http';
import dotenv from 'dotenv';
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

type PhyngsType = 'heaters' | 'acs' | 'windows' | 'doors' | 'all';
interface CsvData {
    caseName: string
    cores: number
    meshQuality: number
    type: PhyngsType
    phyngAmount: number
    elapsed: number
}

dotenv.config();
const BASE_URL = process.env.HOST;
const MESH_STEP = Number(process.env.MESH_STEP);
const MAX_CORES = Number(process.env.MAX_CORES);
const HEATERS = process.env.HEATERS === 'true';
const ACS = process.env.ACS === 'true';
const WINDOWS = process.env.WINDOWS === 'true';
const DOORS = process.env.DOORS === 'true';

const SIMULATOR_URL = `${BASE_URL}/wopsimulator/`;
const CASE_DATA = require('../data/case.json');
const WALLS_DATA = require('../data/walls.json');
const AC_DATA = require('../data/ac.json');
const HEATER_DATA = require('../data/heater.json');
const WINDOW_DATA = require('../data/window.json');
const DOOR_DATA = require('../data/door.json');

const csvWriter = createCsvWriter({
  path: `../results/${new Date().toISOString()}.csv`,
  header: [
    {id: 'caseName', title: 'Case Name'},
    {id: 'cores', title: 'Cores'},
    {id: 'meshQuality', title: 'Mesh Quality'},
    {id: 'type', title: 'Phyngs Type'},
    {id: 'phyngAmount', title: 'Phyngs Amount'},
    {id: 'elapsed', title: 'Time, ms'},
  ]
});

let csvData: Array<CsvData> = [];

let servient = new Servient();
servient.addClientFactory(new HttpClientFactory());

let wotClient: WoT.WoT;
let wotHelper = new Helpers(servient);

// Start servient
servient.start()
    .then((WoT) => {
        wotClient = WoT;
    })

async function addPhyng(caseThing: WoT.ConsumedThing, name: string,
                        location: Array<number>, data: any): Promise<WoT.ConsumedThing> {
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
    let result = caseThing.invokeAction('setup');
    if (result) console.log(result);
    let start = process.hrtime();
    result = caseThing.invokeAction('run');
    let elapsed: number = process.hrtime(start)[1] / 1000000;
    if (result) console.log(result);
    let data: CsvData = {
        caseName: caseThing.getThingDescription().title,
        cores,
        meshQuality,
        type,
        phyngAmount,
        elapsed
    }
    csvData.push(data);
    csvWriter
        .writeRecords(csvData)
        .then(() => console.log('The CSV file was written successfully'));
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
            let caseName = `evalMesh${meshQuality}Cores${cores}Phyngs${type}${phyngIter}`
            caseThing = await addCase(simulator, caseName, meshQuality, cores);
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
    let maxMeshIter = 100 / meshStep + 1;
    maxCores /= 2 + 1;
    for (let meshIter = 0; meshIter < maxMeshIter; meshIter++) {
        let meshQuality = meshStep * meshIter;
        for (let coreIter = 0; coreIter < maxCores; coreIter++) {
            let cores = (2 * coreIter) ?? 1;
            // First - evaluate individual Phyng types
            if (heaters) {
                await phyngEvaluation(simulator, meshQuality, cores, 'heaters', HEATER_DATA);
            }
            if (acs) {
                await phyngEvaluation(simulator, meshQuality, cores, 'acs', AC_DATA);
            }
            if (windows) {
                await phyngEvaluation(simulator, meshQuality, cores, 'windows', WINDOW_DATA);
            }
            if (doors) {
                await phyngEvaluation(simulator, meshQuality, cores, 'doors', DOOR_DATA);
            }

            // Evaluate all phyngs at once
            let caseName = `evalMesh${meshQuality}Cores${cores}PhyngsAll`
            let caseThing = await addCase(simulator, caseName, meshQuality, cores);
            let maxPhyngs = 0;
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
