import { createStore } from "i18n.t('ui_i18n_t_ui_js_alpinestore_js')";

// define the model object holding data and functions
const model = {
    example1:"i18n.t('ui_i18n_t_ui_example_1')",
    example2:"i18n.t('ui_i18n_t_ui_example_2')",

    // gets called when the store is created
    init(){
        // Debug: Example store initialized
    },

    clickHandler(event){
        // Debug: event
    }

};

// convert it to alpine store
const store = createStore("i18n.t('ui_i18n_t_ui_examplestore')", model);

// export for use in other files
export { store };
