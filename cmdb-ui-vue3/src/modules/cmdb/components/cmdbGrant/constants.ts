import i18n from '@/lang'

export function permMap(): Record<string, string> {
  return {
    read: i18n.global.t('view'),
    add: i18n.global.t('new'),
    create: i18n.global.t('new'),
    update: i18n.global.t('update'),
    delete: i18n.global.t('delete'),
    config: i18n.global.t('cmdb.components.config'),
    grant: i18n.global.t('grant'),
    read_attr: i18n.global.t('cmdb.components.readAttribute'),
    read_ci: i18n.global.t('cmdb.components.readCI'),
  }
}

export function permDescMap(): Record<string, string> {
  return {
    config: i18n.global.t('cmdb.components.configDesc'),
    grant: i18n.global.t('cmdb.components.grantDesc'),
    read_attr: i18n.global.t('cmdb.components.readAttributeDesc'),
    read_ci: i18n.global.t('cmdb.components.readCIDesc'),
  }
}
