<template>
<div class="navbar bg-base szoveg" >

    <div class="flex-none">
      <a class="btn btn-ghost text-xl">Liion Töltő</a>
    </div>
    
    <div class="flex-1">
      <ul class="menu menu-horizontal px-1">
        <li><RouterLink class="nav btn btn-ghost" to="/data">Adatok</RouterLink></li>
        <li><RouterLink class="nav btn btn-ghost" to="/history">Korábbi</RouterLink></li>
      </ul>
    </div>

  </div>
</template>

<style>
.szoveg {
  color: #c3c3c6;
  font-family: "Inter", sans-serif;
}
</style>