

import * as device from "i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_device_js')')";

export async function initialize(){
    // set device class to body tag
    setDeviceClass();
}

function setDeviceClass(){
    device.determineInputType().then((type) => i18n.t('i18n.t('ui_i18n_t_ui_remi18n.t('ui_i18n_t_ui_i18n_t_ui_remove_any_class_starting_with_device_from')ody = document.body;
        body.classList.forEach(cls => {
            if (cls.startsWith('i18n.t('ui_device')')) {
                body.classList.remove(cls);
            }
        });
        // Add the new device class
        body.classList.add(`i18n.t('ui_device_type')`);
    });
}
