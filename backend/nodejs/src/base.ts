import {Servient} from '@node-wot/core';
import {HttpServer} from '@node-wot/binding-http';
import axios from 'axios';
const {spawn} = require('child_process');

import {Simulator} from './things';
import {ChtCase} from './objects/cht';

const delay = (ms: number) => new Promise(resolve => {
    setTimeout(() => {
        resolve(2);
    }, ms);
});

let SIMULATION_HOST: string;
let simulationHostAddressResolver: Function;
let simulationHostAddress = new Promise(resolve => {
    simulationHostAddressResolver = resolve;
})
let CASE_PARAMS: { [key: string]: { [key: string]: Function} | { [key: string]: any} } = {
    'cht_room': {
        'constructor': (host: string, wot: WoT.WoT, td: string, name: string) => new ChtCase(host, wot, td, name),
        'td': require('../tms/cht_case.json')
    }
}

const pythonSimulator = spawn('python3', [`${__dirname}/../../python/server.py`]);
pythonSimulator.stdout.on('data', (data: any) => {
    console.log(`${data}`);
});

pythonSimulator.stderr.on('data', (data: any) => {
    let match = data.toString().match('.Running on ([^\\s]*)\\s');
    if (match) {
        SIMULATION_HOST = match[1].substring(0, match[1].length - 1);
        simulationHostAddressResolver(true);
    }
    console.error(`${data}`);
});

let httpServer = new HttpServer({port: 8080});
let servient = new Servient();
servient.addServer(httpServer);

servient.start()
    .then(async (WoT) => {
        await simulationHostAddress;
        let simulator = new Simulator(SIMULATION_HOST, WoT, require('../tms/simulator.json'), CASE_PARAMS);
    })