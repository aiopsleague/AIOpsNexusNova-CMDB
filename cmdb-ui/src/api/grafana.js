import { axios } from '@/utils/request'

export function getGrafanaConnections() {
    return axios({
        url: `/common-setting/v1/grafana/connections`,
        method: 'get',
    })
}

export function postGrafanaConnection(data) {
    return axios({
        url: `/common-setting/v1/grafana/connections`,
        method: 'post',
        data: { data },
    })
}

export function putGrafanaConnection(id, data) {
    return axios({
        url: `/common-setting/v1/grafana/connections/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deleteGrafanaConnection(id) {
    return axios({
        url: `/common-setting/v1/grafana/connections/${id}`,
        method: 'delete',
    })
}

export function testGrafanaConnection(data) {
    return axios({
        url: `/common-setting/v1/grafana/connections/test`,
        method: 'post',
        data: { data },
    })
}

export function getGrafanaMappings() {
    return axios({
        url: `/common-setting/v1/grafana/mappings`,
        method: 'get',
    })
}

export function postGrafanaMapping(data) {
    return axios({
        url: `/common-setting/v1/grafana/mappings`,
        method: 'post',
        data: { data },
    })
}

export function putGrafanaMapping(id, data) {
    return axios({
        url: `/common-setting/v1/grafana/mappings/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deleteGrafanaMapping(id) {
    return axios({
        url: `/common-setting/v1/grafana/mappings/${id}`,
        method: 'delete',
    })
}
