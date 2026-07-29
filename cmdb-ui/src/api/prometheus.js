import { axios } from '@/utils/request'

export function getPrometheusConnections() {
    return axios({
        url: `/common-setting/v1/prometheus/connections`,
        method: 'get',
    })
}

export function postPrometheusConnection(data) {
    return axios({
        url: `/common-setting/v1/prometheus/connections`,
        method: 'post',
        data: { data },
    })
}

export function putPrometheusConnection(id, data) {
    return axios({
        url: `/common-setting/v1/prometheus/connections/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deletePrometheusConnection(id) {
    return axios({
        url: `/common-setting/v1/prometheus/connections/${id}`,
        method: 'delete',
    })
}

export function testPrometheusConnection(data) {
    return axios({
        url: `/common-setting/v1/prometheus/connections/test`,
        method: 'post',
        data: { data },
    })
}

export function getPrometheusConnectionsHealth() {
    return axios({
        url: `/common-setting/v1/prometheus/connections/health`,
        method: 'get',
    })
}

export function getPrometheusMappings() {
    return axios({
        url: `/common-setting/v1/prometheus/mappings`,
        method: 'get',
    })
}

export function postPrometheusMapping(data) {
    return axios({
        url: `/common-setting/v1/prometheus/mappings`,
        method: 'post',
        data: { data },
    })
}

export function putPrometheusMapping(id, data) {
    return axios({
        url: `/common-setting/v1/prometheus/mappings/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deletePrometheusMapping(id) {
    return axios({
        url: `/common-setting/v1/prometheus/mappings/${id}`,
        method: 'delete',
    })
}
