import { createRouter, createWebHistory } from "vue-router";
import GearList from "./views/GearList.vue";
import GearEdit from "./views/GearEdit.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: GearList },
    { path: "/gear/:id", component: GearEdit, props: true },
  ],
});

export default router;
