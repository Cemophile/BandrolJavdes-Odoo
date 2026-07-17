/** @odoo-module **/

import { registry } from "@web/core/registry";

const bandrolRefreshService = {
    dependencies: ["bus_service", "action"],
    start(env, { bus_service, action }) {
        bus_service.addChannel("bandrol_islem_kanal");

        bus_service.addEventListener("notification", ({ detail: notifications }) => {
            for (const { payload, type } of notifications) {
                if (type === "bandrol_guncelleme") {

                    if (window.location.hash.includes("model=orduevi.transaction")) {
                        action.doAction({ type: "ir.actions.client", tag: "reload" });
                    }
                }
            }
        });
    }
};

registry.category("services").add("orduevi_bandrol_refresh", bandrolRefreshService);