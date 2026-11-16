<script setup lang="ts">
defineProps<{ name: string; size?: number }>()
const paths: Record<string, string> = {
  inbox: 'M4 4h16v16H4z M4 14h5l2 3h2l2-3h5',
  spark: 'm12 3 2.8 6.2L21 12l-6.2 2.8L12 21l-2.8-6.2L3 12l6.2-2.8Z',
  orders: 'M7 3h10v4H7z M7 5H4v16h16V5h-3 M8 12h8 M8 16h5',
  book: 'M3 4h7l2 2 2-2h7v16h-7l-2 1-2-1H3z M12 6v15',
  search: 'M16 16l5 5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
  plus: 'M12 5v14 M5 12h14',
  arrow: 'M4 12h16 M14 6l6 6-6 6',
  send: 'm3 3 18 9-18 9 4-9-4-9 M7 12h14',
  close: 'm6 6 12 12 M18 6 6 18',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  file: 'M14 2H5v20h14V7l-5-5 M14 2v6h5 M8 12h8 M8 16h6',
  logout: 'M9 3H4v18h5 M13 7l5 5-5 5 M8 12h13',
  check: 'm5 12 4 4 10-10',
  refresh: 'M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 2 M18 18a8 8 0 0 1-13-2',
  chevron: 'm9 5 7 7-7 7',
  stop: 'M6 6h12v12H6z',
}
</script>
<template>
  <svg
    :width="size ?? 20"
    :height="size ?? 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] ?? paths.spark" />
  </svg>
</template>
