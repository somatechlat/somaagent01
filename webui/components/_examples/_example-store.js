import { createStore } from "/static/js/AlpineStore.js";

// define the model object holding data and functions
const model = {
    example1:"Example 1",
    example2:"Example 2",

    // gets called when the store is created
    init(){
        // Debug: Example store initialized
    },

    clickHandler(event){
        // Debug: event
    }

};

// convert it to alpine store
const store = createStore("_exampleStore", model);

// export for use in other files
export { store };
