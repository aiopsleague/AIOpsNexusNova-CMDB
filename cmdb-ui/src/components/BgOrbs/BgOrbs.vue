<template>
  <div class="bg-orbs" aria-hidden="true">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
  </div>
</template>

<script>
/**
 * BgOrbs — animated neon background blobs (霓虹光斑) for the dark/glass theme.
 *
 * All visuals live in src/style/themes/dark-overrides.less, so the layer only
 * renders when dark.css is loaded (dark mode). In light mode the wrapper is
 * hard-hidden by a guard rule in global.less (html:not([data-theme='dark'])).
 */
export default {
  name: 'BgOrbs'
}
</script>
