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
    const SETTINGS_COLLECTION = "67de7e600036fcfc5959";

    try {
        const chargerSetting = await databases.listDocuments(DB_ID, SETTINGS_COLLECTION, [
            Query.equal("setting_name", "CHARGER_SWITCH"),
            Query.limit(1)
        ]);

        // Ha be van kapcsolva → első töltő aktív (mode = 1), második nem
        // Ha ki van kapcsolva → második töltő aktív (mode = 2), első nem
        const isFirstChargerActive = chargerSetting.total > 0 ? chargerSetting.documents[0].setting_boolean : true;
        const chargerMode = isFirstChargerActive ? 1 : 2;

        const batteries = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
            Query.equal("status", 3),
            Query.equal("operation", 1),
            Query.limit(100)
        ]);

        const rechargeBatteries = await databases.listDocuments(DB_ID, BATTERY_COLLECTION, [
            Query.equal("status", 5),
            Query.equal("operation", 1),
            Query.limit(100)
        ]);

        if (batteries.total === 0 && rechargeBatteries.total === 0) {
            log("No batteries currently charging or recharging.");
            return res.json({ message: "No batteries currently charging or recharging." });
        }

        for (const battery of [...batteries.documents, ...rechargeBatteries.documents]) {
            if (chargerMode === 1 && !battery.open_circuit) {
                log(`Battery ${battery.$id} még nem mért feszültséget első töltő előtt.`);
                continue;
            }

            const allChargeEntries = await databases.listDocuments(DB_ID, CHARGE_COLLECTION, [
                Query.equal("battery", battery.$id),
                Query.equal("mode", chargerMode),
                Query.equal("open_circuit", false),
                Query.orderAsc("$createdAt"),
                Query.limit(100)
            ]);

            if (allChargeEntries.total === 0) continue;

            const latest = allChargeEntries.documents[allChargeEntries.total - 1];
            const chargeCurrent = latest.chargecurrent ?? null;
            const feszultseg = latest.voltage ?? null;
            const open_circuit = latest.open_circuit ?? false;
            const belsoEllenallas = (chargeCurrent && feszultseg) ? feszultseg / chargeCurrent : null;

            await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                ...(feszultseg !== null && { feszultseg }),
                ...(open_circuit !== null && { open_circuit }),
                ...(chargeCurrent !== null && { chargecurrent: chargeCurrent }),
                ...(belsoEllenallas !== null && { belso_ellenallas: belsoEllenallas }),
                ...(latest.charge_capacity !== undefined && { charge_capacity: latest.charge_capacity }),
                ...(battery.charging_started_at ? {} : { charging_started_at: new Date().toISOString() })
            });

            // kiszámoljuk a teljes töltési ciklus kapacitását (mAh)
            if (allChargeEntries.total >= 2) {
                const firstCap = allChargeEntries.documents[0].charge_capacity;
                const lastCap = allChargeEntries.documents[allChargeEntries.total - 1].charge_capacity;

                if (firstCap !== undefined && lastCap !== undefined) {
                    const measuredCapacity = lastCap - firstCap;
                    await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                        ...(battery.status === 3 ? { charge_capacity: measuredCapacity } : {}),
                        ...(battery.status === 5 ? { recharge_capacity: measuredCapacity } : {})
                    });
                }
            }

            // státusz váltások
            if (battery.status === 3 && open_circuit && feszultseg >= 4.2) {
                await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                    status: 4,
                    operation: 0,
                    charging_started_at: null
                });
            }

            if (battery.status === 5 && open_circuit && feszultseg >= 4.2) {
                await databases.updateDocument(DB_ID, BATTERY_COLLECTION, battery.$id, {
                    status: 7,
                    operation: 0,
                    charging_started_at: null
                });
            }
        }

        // kapcsoló átállítása töltőváltáshoz csak ha utolsó töltési adat 5 percnél régebbi
        const latestCharge = await databases.listDocuments(DB_ID, CHARGE_COLLECTION, [
            Query.orderDesc("$createdAt"),
            Query.limit(1)
        ]);

        if (latestCharge.total > 0) {
            const lastTime = new Date(latestCharge.documents[0].$createdAt);
            const now = new Date();
            const diffMinutes = (now - lastTime) / 60000;

            if (diffMinutes >= 5) {
                await databases.updateDocument(DB_ID, SETTINGS_COLLECTION, chargerSetting.documents[0].$id, {
                    setting_boolean: !isFirstChargerActive
                });
                log(`CHARGER_SWITCH átkapcsolva (${!isFirstChargerActive ? 'első' : 'második'} töltő aktiválva).`);
            } else {
                log("Túltöltési váltás kihagyva: még nincs 5 perc az utolsó töltés óta.");
            }
        }

        log("Charging check completed.");
        return res.json({ message: "Charging check completed." });
    } catch (err) {
        error("Hiba:", err);
        return res.json({ error: err.message });
    }
}
