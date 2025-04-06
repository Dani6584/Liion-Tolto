<template>
<div class="navbar bg-base szoveg">

  <div class="flex-none">
    <a class="btn btn-ghost text-xl">Liion Töltő</a>
  </div>
  <div class="flex-1">
    <ul class="menu menu-horizontal px-1">
      <li class="hidden md:block lg:block"><RouterLink class="nav btn btn-ghost" to="/data">Folyamatban</RouterLink></li>
      <li class="hidden md:block lg:block"><RouterLink class="nav btn btn-ghost" to="/history">Korábbi</RouterLink></li>
      <li class="hidden md:block lg:block"><RouterLink class="nav btn btn-ghost" to="/ocr">OCR</RouterLink></li>

      <li class="md:hidden">
        <details ref="dropdown">
          <summary class="nav btn btn-ghost pt-4">Menüpontok</summary>
          <ul class="bg-base-100 rounded-t-none">
            <li><RouterLink class="nav btn btn-ghost" to="/data" @click="closeMenu">Folyamatban</RouterLink></li>
            <li><RouterLink class="nav btn btn-ghost" to="/history" @click="closeMenu">Korábbi</RouterLink></li>
            <li><RouterLink class="nav btn btn-ghost" to="/ocr" @click="closeMenu">OCR</RouterLink></li>
          </ul>
        </details>
      </li>

    </ul>
  </div>
  
</div>
</template>

<script>
export default {
  methods: {
    closeMenu() {
      const details = this.$el.querySelector('details');
      details.removeAttribute('open');
    },
    handleClickOutside(event) {
      const details = this.$refs.dropdown;
      if (details && !details.contains(event.target)) { // Ha a dropdown-on kívül kattintok akkor becsukja
        this.closeMenu();
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeDestroy() {
    document.removeEventListener('click', this.handleClickOutside);
  }
}
</script>


<style>
details[open] {
  z-index: 50; /*Legfelso réteg*/
}
.szoveg {
  color: #c3c3c6;
  font-family: "Inter", sans-serif;
}
</style>