import {Servient} from '@node-wot/core';
import {HttpServer} from '@node-wot/binding-http';

import {CaseConstructorType, Simulator} from './base/simulator';
import {ChtCase} from './behavior/cht';

const {spawn} = require('child_process');

const delay = (ms: number) => new Promise(resolve => {
    setTimeout(() => {
        resolve(2);
    }, ms);
});

let SIMULATION_HOST: string = 'http://127.0.0.1:5000';
let simulationHostAddressResolver: Function;
let simulationHostAddress = new Promise(resolve => {
    simulationHostAddressResolver = resolve;
})
let CASE_PARAMS: CaseConstructorType = {
    'cht_room': {
        'constructor': (host: string, wot: WoT.WoT,
                        tm: WoT.ThingDescription, name: string) => new ChtCase(host, wot, tm, name),
        'tm': require('../tms/behavior/cht/case.model.json')
    }
}

// const pythonSimulator = spawn('python3', [`${__dirname}/../../python/server.py`]);
// pythonSimulator.stdout.on('data', (data: any) => {
//     console.log(`${data}`);
// });
//
// pythonSimulator.stderr.on('data', (data: any) => {
//     let match = data.toString().match('.Running on ([^\\s]*)\\s');
//     if (match) {
//         SIMULATION_HOST = match[1].substring(0, match[1].length - 1);
//         simulationHostAddressResolver(true);
//     }
//     console.error(`${data}`);
// });

let httpServer = new HttpServer({port: 8080});
let servient = new Servient();
servient.addServer(httpServer);

servient.start()
    .then(async (WoT) => {
        // await simulationHostAddress;
        let simulator = new Simulator(SIMULATION_HOST, WoT, require('../tms/simulator.model.json'), CASE_PARAMS);
    })
