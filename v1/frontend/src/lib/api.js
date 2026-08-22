import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const client = axios.create({
    baseURL: API_BASE,
    timeout: 25000,
});

export async function fetchStations() {
    const { data } = await client.get("/stations");
    return data;
}

export async function fetchStation(id) {
    const { data } = await client.get(`/stations/${id}`);
    return data;
}

export async function refreshStation(id) {
    const { data } = await client.post(`/stations/${id}/refresh`);
    return data;
}

export async function refreshAllStations() {
    const { data } = await client.post(`/refresh`);
    return data;
}

export async function fetchSystemStatus() {
    const { data } = await client.get("/system/status");
    return data;
}
