import axios from 'axios';

export class HeatingProperties {
    public async getTemperature(url: string) {
        let response = await axios.get(`${url}/temperature`);
        return response.data;
    }

    public async setTemperature(url: string, temperature: number) {
        await axios.post(`${url}/temperature`, {value: temperature});
    }

    protected setTemperatureGetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setPropertyReadHandler('temperature', async () => {
            return await this.getTemperature(url);
        });
    }

    protected setTemperatureSetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setPropertyWriteHandler('temperature', async (temperature) => {
            await this.setTemperature(url, temperature);
        });
    }
}

export class VelocityProperties {
    public async getVelocity(url: string) {
        let response = await axios.get(`${url}/velocity`);
        return response.data;
    }

    public async setVelocity(url: string, velocity: Array<number>) {
        await axios.post(`${url}/velocity`, {value: velocity});
    }

    protected setVelocityGetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setPropertyReadHandler('velocity', async () => {
            return await this.getVelocity(url);
        });
    }

    protected setVelocitySetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setPropertyWriteHandler('velocity', async (velocity) => {
            await this.setVelocity(url, velocity);
        });
    }
}

export class OpenableProperties {
    public async getOpen(url: string) {
        let response = await axios.get(`${url}/open`);
        return response.data;
    }

    public async setOpen(url: string, open: boolean) {
        await axios.post(`${url}/open`, {value: open});
    }

    protected setOpenGetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setPropertyReadHandler('opened', async () => {
            return await this.getOpen(url);
        });
    }

    protected setOpenSetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setActionHandler('open', async () => {
            await this.setOpen(url, true);
        });
    }

    protected setCloseSetHandler(thing: WoT.ExposedThing, url: string) {
        thing.setActionHandler('close', async () => {
            await this.setOpen(url, false);
        });
    }
}
