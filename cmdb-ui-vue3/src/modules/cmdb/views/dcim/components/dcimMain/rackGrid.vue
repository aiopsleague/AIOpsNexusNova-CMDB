<script setup lang="ts">
import { WarningFilled, RightOutlined, DatabaseOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import rackImg from '@/assets/dcim/rack.png'
import dataEmptyImg from '@/assets/data_empty.png'

withDefaults(
  defineProps<{
    rackList?: any[]
  }>(),
  {
    rackList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'openRackDetail', data: any): void
}>()

const { t } = useI18n()

function openRackDetail(data: any) {
  emit('openRackDetail', data)
}
</script>

<template>
  <div class="rack-grid">
    <template v-if="rackList.length">
      <div v-for="(item, index) in rackList" :key="index" class="rack-grid-item">
        <div v-if="item.u_slot_abnormal" class="rack-grid-item-warning">
          <WarningFilled class="rack-grid-item-warning-icon" />
          <span class="rack-grid-item-warning-text">
            {{ t('cmdb.dcim.unitAbnormal') }}
          </span>
        </div>

        <div class="rack-grid-item-header">
          <a-tooltip :title="item.name">
            <div class="rack-grid-item-name">
              {{ item.name }}
            </div>
          </a-tooltip>
          <div class="rack-grid-item-store">
            {{ `${item.u_count || 0}U` }}
          </div>
        </div>

        <img class="rack-grid-item-img" :src="rackImg" />

        <div class="rack-grid-item-data">
          <DatabaseOutlined class="rack-grid-item-data-icon" />
          <span class="rack-grid-item-data-value">
            {{ item.u_used_count }}/{{ item.u_count }}
          </span>

          <div class="rack-grid-item-data-progress">
            <div class="rack-grid-item-data-progress-line" :style="{ width: item.u_used_ratio + '%' }"></div>
            <div class="rack-grid-item-data-progress-end" :style="{ left: item.u_used_ratio + '%' }"></div>
          </div>
        </div>

        <a class="rack-grid-item-btn" @click="openRackDetail(item)">
          <span class="rack-grid-item-btn-text">{{ t('cmdb.dcim.viewDetail') }}</span>
          <RightOutlined class="rack-grid-item-btn-icon" />
        </a>
      </div>
    </template>

    <div v-else class="rack-grid-null">
      <img class="rack-grid-null-img" :src="dataEmptyImg" />
      <div class="rack-grid-null-text">{{ t('noData') }}</div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.rack-grid {
  display: flex;
  flex-wrap: wrap;
  column-gap: 27px;
  row-gap: 27px;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: 100%;
  padding-bottom: 57px;

  &-item {
    width: 205px;
    height: 219px;
    flex-shrink: 0;
    background-color: #f9fbff;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
    cursor: pointer;
    text-align: center;
    transition: all 0.1s;

    &-warning {
      display: flex;
      align-items: center;
      padding: 2px 6px;
      background-color: #ffdebf;
      border-radius: 2px;
      width: max-content;

      position: absolute;
      top: 30px;
      left: 50%;
      transform: translateX(-50%);

      &-icon {
        font-size: 12px;
        color: #ff7d00;
        margin-right: 2.5px;
      }

      &-text {
        font-size: 12px;
        font-weight: 400;
        color: #ff7d00;
      }

      &::after {
        content: '';
        position: absolute;
        bottom: -6px;
        left: 50%;
        margin-left: -7px;

        width: 0;
        height: 0;
        border-left: 7px solid transparent;
        border-right: 7px solid transparent;
        border-top: 6px solid #ffdebf;
      }
    }

    &-header {
      width: 100%;
      height: 25px;
      background-color: #8fb9f712;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    &-name {
      height: 25px;
      line-height: 25px;
      border-bottom-right-radius: 25px;
      padding-left: 7px;
      padding-right: 17px;
      background-color: #4e5969;

      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    &-store {
      padding-right: 10px;
      font-size: 14px;
      font-weight: 400;
      color: #2f54eb;
      margin-left: 12px;
    }

    &-img {
      height: 112px;
      margin-top: 16px;
      transition: all 0.1s;
    }

    &-data {
      margin-top: 16px;
      display: flex;
      align-items: center;
      justify-content: center;

      &-icon {
        font-size: 16px;
      }

      &-value {
        margin-left: 5px;
        font-size: 14px;
        font-weight: 400;
        color: #4e5969;
      }

      &-progress {
        margin-left: 6px;
        width: 97px;
        height: 2px;
        border-radius: 2px;
        background-color: #c3d0eb;
        position: relative;

        &-line {
          height: 2px;
          border-radius: 2px;
          background-color: #7f97fa;
        }

        &-end {
          position: absolute;
          top: 50%;
          margin-top: -8px;
          margin-left: -8px;
          height: 16px;
          width: 16px;
          border-radius: 16px;
          background-color: #3044f112;

          &::after {
            content: '';
            position: absolute;
            z-index: 2;
            top: 50%;
            left: 50%;
            margin-top: -3px;
            margin-left: -3px;
            background-color: #2f54eb;
            width: 6px;
            height: 6px;
            border-radius: 6px;
          }
        }
      }
    }

    &-btn {
      position: absolute;
      right: 17px;
      bottom: 10px;
      align-items: center;
      display: none;

      &-text {
        margin-right: 2px;
        font-size: 12px;
        font-weight: 400;
        color: #2f54eb;
      }

      &-icon {
        font-size: 12px;
        color: #2f54eb;
      }
    }

    &:hover {
      background-color: #ffffff;
      box-shadow: 0px 22px 33px 0px #2f54eb15;
      z-index: 2;

      .rack-grid-item-name {
        background-color: #2f54eb;
      }

      .rack-grid-item-img {
        margin-top: 7px;
        height: 128px;
      }

      .rack-grid-item-data {
        margin-top: 9px;

        &-icon {
          display: none;
        }

        &-progress {
          width: 112px;
        }
      }

      .rack-grid-item-btn {
        display: flex;
      }
    }
  }

  &-null {
    padding-top: 150px;
    text-align: center;
    width: 100%;

    &-img {
      width: 150px;
    }

    &-text {
      margin-top: 12px;
    }
  }
}
</style>
