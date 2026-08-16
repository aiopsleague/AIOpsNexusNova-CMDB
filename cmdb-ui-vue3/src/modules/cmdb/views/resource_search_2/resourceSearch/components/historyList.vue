<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DeleteOutlined, CloseOutlined, DownOutlined, EyeOutlined, StarFilled, StarOutlined } from '@ant-design/icons-vue'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'

withDefaults(
  defineProps<{
    recentList?: any[]
    favorList?: any[]
    detailCIId?: string | number
  }>(),
  {
    recentList: () => [],
    favorList: () => [],
    detailCIId: -1,
  }
)

const emit = defineEmits<{
  (e: 'clickRecent', data: any): void
  (e: 'deleteRecent', id: string | number): void
  (e: 'clearRecent'): void
  (e: 'deleteCollect', id: string | number): void
  (e: 'showDetail', data: { id: string | number; ciTypeId: string | number }): void
}>()

const { t } = useI18n()

const isExpand = ref(false)

function getRecentSearchText(option: Record<string, any>): string {
  const textArray: string[] = []
  if (option.searchValue) {
    textArray.push(`${t('cmdb.ciType.keyword')}: ${option.searchValue}`)
  }

  if (option?.ciTypeNames?.length) {
    textArray.push(`${t('cmdb.ciType.CIType')}: ${option.ciTypeNames.join(',')}`)
  }

  if (option.expression) {
    textArray.push(`${t('cmdb.ciType.conditionFilter')}: ${option.expression}`)
  }

  return textArray.join('; ')
}

function clickRecent(data: any) {
  emit('clickRecent', data)
}

function deleteRecent(id: string | number) {
  emit('deleteRecent', id)
}

function deleteCollect(id: string | number) {
  emit('deleteCollect', id)
}

function showDetail(data: any) {
  emit('showDetail', {
    id: data.CIId,
    ciTypeId: data.CITypeId,
  })
}

function clearRecent() {
  emit('clearRecent')
}
</script>

<template>
  <div class="history-list">
    <div v-if="recentList.length" class="history-recent">
      <div class="history-title">
        <EyeOutlined class="history-title-icon" />
        <div class="history-title-text">{{ t('cmdb.ciType.recentSearch') }}</div>

        <a-popconfirm :title="t('cmdb.ciType.confirmClear')" placement="topRight" @confirm="clearRecent">
          <a-tooltip :title="t('clear')">
            <DeleteOutlined class="history-title-clear" />
          </a-tooltip>
        </a-popconfirm>
      </div>
      <div class="recent-list">
        <div
          v-for="item in recentList.slice(0, 10)"
          :key="item.id"
          class="recent-list-item"
          @click="clickRecent(item.option)"
        >
          <div class="recent-list-item-text">
            {{ getRecentSearchText(item.option) }}
          </div>
          <CloseOutlined class="recent-list-item-close" @click.stop="deleteRecent(item.id)" />
        </div>
      </div>
    </div>

    <div v-if="favorList.length" class="history-favor">
      <div class="history-title">
        <StarOutlined class="history-title-icon" />
        <div class="history-title-text">{{ t('cmdb.ciType.myCollection') }}</div>
        <div class="history-title-count">({{ favorList.length }})</div>

        <DownOutlined
          class="history-title-expand"
          :style="{
            transform: `rotate(${isExpand ? '180deg' : '0deg'})`,
          }"
          @click="isExpand = !isExpand"
        />
      </div>
      <div class="favor-list" :style="{ height: isExpand ? 'auto' : '30px' }">
        <div
          v-for="item in favorList"
          :key="item.id"
          :class="['favor-list-item', detailCIId === item.option.CIId ? 'favor-list-item-selected' : '']"
          @click="showDetail(item.option)"
        >
          <CIIcon :icon="item.option.icon" :title="item.option.CITypeTitle" />
          <div class="favor-list-item-title">
            {{ item.option.title }}
          </div>
          <StarFilled class="favor-list-item-collected" @click.stop="deleteCollect(item.id)" />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.history-list {
  width: 100%;

  .history-title {
    display: flex;
    align-items: center;

    &-icon {
      font-size: 12px;
      color: #2f54eb;
    }

    &-text {
      font-size: 14px;
      font-weight: 400;
      color: #4e5969;
      margin-left: 4px;
    }

    &-count {
      font-size: 14px;
      font-weight: 400;
      color: #86909c;
    }

    &-clear {
      margin-left: auto;
      cursor: pointer;
    }

    &-expand {
      margin-left: auto;
      cursor: pointer;
    }
  }

  .history-recent {
    width: 100%;
    margin-top: 15px;

    .recent-list {
      margin-top: 10px;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      column-gap: 16px;
      row-gap: 8px;

      &-item {
        flex-shrink: 0;
        padding: 4px 13px;
        display: flex;
        align-items: center;
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        max-width: calc((100% - 16px) / 2);

        &-text {
          font-size: 12px;
          font-weight: 400;
          color: #1d2129;

          max-width: 100%;
          text-wrap: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }

        &-close {
          font-size: 12px;
          margin-left: 4px;
          color: #a5a9bc;
          display: none;
        }

        &:hover {
          .recent-list-item-text {
            color: #2f54eb;
          }

          .recent-list-item-close {
            display: inline-block;
          }
        }
      }
    }
  }

  .history-favor {
    width: 100%;
    margin-top: 15px;

    .favor-list {
      margin-top: 10px;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      column-gap: 16px;
      row-gap: 8px;
      overflow: hidden;
      min-height: 30px;

      &-item {
        flex-shrink: 0;
        padding: 4px 13px;
        display: flex;
        align-items: center;
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.9);
        cursor: pointer;
        max-width: calc((100% - 16px) / 2);

        &-title {
          font-size: 12px;
          font-weight: 400;
          margin-left: 4px;
          color: #1d2129;

          max-width: 100%;
          text-overflow: ellipsis;
          text-wrap: nowrap;
          overflow: hidden;
        }

        &-collected {
          font-size: 14px;
          margin-left: 4px;
          color: #fad337;
        }

        &-selected {
          border: 1px solid #7f97fa;
          background-color: rgba(255, 255, 255, 0.9);

          .favor-list-item-title {
            color: #2f54eb;
          }
        }

        &:hover {
          .favor-list-item-title {
            color: #2f54eb;
          }
        }
      }
    }
  }
}
</style>
