import { Client, Databases, Query } from "node-appwrite";

export default async ({ req, res, log, error }) => {
    const client = new Client()
        .setEndpoint("https://appwrite.tsada.edu.rs/v1")
        .setProject("67a5b2fd0036cbf53dbf")
        .setKey("standard_cd198d0d53bf431d78706ab420ce6841ae4d7bf7354d22ff6b40c88a7b8403c826c6eccf1aabbe5b3e720fae15b720bc870edb2b562557a5084e7fcba1b83788e56f864aed5ae9d647672fb19872b21408900f1e75c97958175ec728d225e0d7b59dd1ce702e1aef869d2a5285774a6a553789c091d62c47f0e02051fc244ac0");

    const databases = new Databases(client);
    const DB_ID = "67a5b54c00004b1a93d7";
    const BATTERY_COLLECTION = "67f279860016263782ae";
    const CHARGE_COLLECTION = "67d18e17000dc1b54f39";

    try {
        const batteries = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
            Query.equal("status", 3),
            Query.equal("operation", 1),
            Query.limit(100)
        ]);

        if (batteries.total === 0) {
            log("No batteries currently charging.");
        return res.json({ message: "No batteries currently charging." });
        }

        for (const battery of batteries.documents) {
            // open_circuit, feszultseg, chargecurrent mostantól a CHARGE_COLLECTION-ből jön
            // lekérés a legutóbbi töltési adathoz
            const chargeEntry = await databases.listDocuments(DB_ID, CHARGE_COLLECTION, [
                Query.equal("battery", battery.$id),
                Query.orderDesc("$createdAt"),
                Query.limit(1)
            ]);

            if (chargeEntry.total === 0) continue;
            const latest = chargeEntry.documents[0];

            const chargeCurrent = latest.chargecurrent ?? null;
            const feszultseg = latest.feszultseg ?? null;
            const open_circuit = latest.open_circuit ?? false;

            const belsoEllenallas = (chargeCurrent && feszultseg) ? feszultseg / chargeCurrent : null;

            await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                ...(feszultseg !== null && { feszultseg }),
                ...(open_circuit !== null && { open_circuit }),
                ...(chargeCurrent !== null && { chargecurrent: chargeCurrent }),
                ...(belsoEllenallas !== null && { belso_ellenallas: belsoEllenallas }),
                ...(latest.chargecapacity !== undefined && { chargecapacity: latest.chargecapacity })
            });

            if (!open_circuit || feszultseg === null) continue;

            // második lekérés törölve – felesleges ismétlés

            const chargeCurrent_2 = latest.chargecurrent ?? null;
            const belsoEllenallasFinal = chargeCurrent_2 && battery.feszultseg ? battery.feszultseg / chargeCurrent_2 : null;

            if (battery.feszultseg >= 4.2) {
                await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                    status: 4,
                    operation: 0,
                    ...(belsoEllenallas !== null && { belso_ellenallas: belsoEllenallasFinal })
                });
            }
        }

        log("Charging check completed.");
        return res.json({ message: "Charging check completed." });
    } catch (err) {
        error("Hiba:", err);
        return res.json({ error: err.message });
    }
}
