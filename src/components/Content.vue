<script setup>
    import { RouterView } from 'vue-router'
    import graph from '@/charts/graph.vue'
</script>

<template>
    <div></div>
    
    <div><graph/></div>

    <div class="grid grid-cols-3 gap-4">
        
        <div class="bg-base-300 rounded-box h-20 col-span-3">
            
        </div>
        
        
        <div class="grid bg-base-300 rounded-box h-20 place-items-center"><RouterView/></div>
        <div class="bg-base-300 rounded-box h-20">3</div>
        <div class="bg-base-300 rounded-box h-20">4</div>

    </div>
    
</template>

