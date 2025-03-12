<script setup>
  import { RouterLink } from 'vue-router'
</script>

<template>  
<div class="bar bg-base">  
  <div class="navbar bg-base" >
    
    <div class="flex-none">
      <a class="btn btn-ghost text-xl">Liion Töltő</a>
    </div>
    <div class="flex-1 ">
      <ul class="menu menu-horizontal px-1">
        <li><RouterLink class="nav btn btn-ghost" to="/data">Adatok</RouterLink></li>
        <li><a class="nav btn btn-ghost">Korábbi</a></li>
      </ul>
    </div>

  </div>
</div>

</template>

<style scoped>
</style>