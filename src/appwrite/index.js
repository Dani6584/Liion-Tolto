import { Client, Databases} from 'appwrite';
export const client = new Client();

client
    .setEndpoint('https://appwrite.tsada.edu.rs/v1')
    .setProject('67a5b2fd0036cbf53dbf')
export const database = new Databases(client);
