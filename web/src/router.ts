import { createRouter, createWebHistory } from "vue-router";
import GearList from "./views/GearList.vue";
import GearEdit from "./views/GearEdit.vue";
import KeywordList from "./views/KeywordList.vue";
import SpecialRuleList from "./views/SpecialRuleList.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: GearList },
    { path: "/gear/:id", component: GearEdit, props: true },
    { path: "/keywords", component: KeywordList },
    { path: "/special-rules", component: SpecialRuleList },
  ],
});

export default router;
