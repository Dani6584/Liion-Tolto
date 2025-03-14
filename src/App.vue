<template>
<div class="select-none">
  <div><Navigation/></div>
  <div class="content grow"><RouterView/></div>
  <div v-if="false" class="z-50"><Footer/></div>
</div>
</template>

<script setup>
  import Navigation from '@/components/Navigation.vue'
  import Footer from '@/components/Footer.vue'
</script>

