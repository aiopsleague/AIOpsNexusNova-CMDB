// DCIM domain constants (migrated from `cmdb-ui/src/modules/cmdb/views/dcim/constants.js`).

export const DCIM_TYPE = {
  REGION: 'region',
  IDC: 'idc',
  SERVER_ROOM: 'server_room',
  RACK: 'rack',
} as const

export const DCIM_CITYPE_NAME = {
  REGION: 'dcim_region',
  IDC: 'dcim_idc',
  SERVER_ROOM: 'dcim_server_room',
  RACK: 'dcim_rack',
} as const

export const DEVICE_CITYPE_NAME = {
  SWITCH: 'switch',
  FC_SWITCH: 'fc_switch',
  F5: 'bigip',
  ROUTER: 'router',
  FIRE_WALL: 'firewall',
  SERVER: 'server',
  RAID: 'raid',
} as const

/**
 * Unit numbering direction.
 * bottom_to_top: bottom to top
 * top_to_bottom: top to bottom
 */
export const U_NUMBERING_DIRECTION = {
  BOTTOM_TO_TOP: 'bottom_to_top',
  TOP_TO_BOTTOM: 'top_to_bottom',
} as const

function createTypeNameMap<T extends Record<string, string>, U extends Record<string, string>>(
  typeObj: T,
  typeNameObj: U
): Record<string, string> {
  const map: Record<string, string> = {}

  Object.keys(typeObj).forEach((key) => {
    map[typeObj[key as keyof T]] = typeNameObj[key as keyof U]
    map[typeNameObj[key as keyof U]] = typeObj[key as keyof T]
  })

  return map
}

export const DCIM_TYPE_NAME_MAP = createTypeNameMap(DCIM_TYPE, DCIM_CITYPE_NAME)
