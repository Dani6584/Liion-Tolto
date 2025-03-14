<template>
<div class="select-none">
  <div><Navigation/></div>
  <div class="content"><RouterView/></div>
  <div v-if="false"><Footer/></div>
</div>

<!--
<div class="select-none flex flex-col min-h-screen">
  <div><Navigation/></div>
  <div class="grow content"><RouterView/></div>
  <div><Footer/></div>
</div>
-->

</template>

<script setup>
  import Navigation from '@/components/Navigation.vue'
  import Footer from '@/components/Footer.vue'
</script>

