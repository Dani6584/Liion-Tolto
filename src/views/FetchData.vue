

<template>
  <div>
    <h1>Appwrite Data</h1>
    <ul>
      <li v-for="item in data" :key="item.$id">{{ item.name }}</li>
    </ul>
  </div>
</template>

<script>
import { databases } from '../appwrite';
import ids from './ids.json';

export default {
  data() {
    return {
      data: []
    };
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    async fetchData() {
      try {
        const response = await databases.listDocuments( ids.database_id, akkumulator_id);
        this.data = response.documents;
      } catch (error) {
        console.error('Error fetching data from Appwrite:', error);
      }
    }
  }
};
</script>
