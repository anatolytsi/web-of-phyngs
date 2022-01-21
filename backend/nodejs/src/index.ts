import {Servient} from '@node-wot/core';
import {HttpServer} from '@node-wot/binding-http';

import {CaseConstructorType, Simulator} from './base/simulator';
import {ChtCase} from './behavior/cht';
import {chtSdSchema} from './base/schemas';

let CASE_PARAMS: CaseConstructorType = {
    'cht': {
        'constructor': (host: string, wot: WoT.WoT,
                        tm: WoT.ThingDescription, name: string) => new ChtCase(host, wot, tm, name),
        'tm': require('../tms/behavior/cht/chtCase.model.json'),
        'sdValidator': chtSdSchema
    }
}

let httpServer = new HttpServer({port: 8080});
let servient = new Servient();
servient.addServer(httpServer);

servient.start()
    .then(async (WoT) => {
        let pythonHost: string = process.env.PYTHON_SERVER || 'http://127.0.0.1:5000';
        let simulator = new Simulator(pythonHost, WoT, require('../tms/simulator.model.json'), CASE_PARAMS);
    })
