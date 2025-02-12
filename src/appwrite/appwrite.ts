import { Client, Databases} from 'appwrite';
export const client = new Client();

client
    .setEndpoint('https://appwrite.tsada.edu.rs')
    .setProject('67a5b2fd0036cbf53dbf');
export const databases = new Databases(client);
