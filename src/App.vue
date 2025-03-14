<script setup>
  import Navigation from '@/components/Navigation.vue'
  import Footer from '@/components/Footer.vue'
</script>

<template>
  <div><Navigation/></div>
  <div class="content grow"><RouterView/></div>
  <div class="z-50"><Footer/></div>
</template>