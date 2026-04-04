import { createRouter, createWebHistory } from "vue-router";
import GearList from "./views/GearList.vue";
import GearEdit from "./views/GearEdit.vue";
import KeywordList from "./views/KeywordList.vue";
import SpecialRuleList from "./views/SpecialRuleList.vue";
import LocationList from "./views/LocationList.vue";
import ExpansionList from "./views/ExpansionList.vue";
import VersionList from "./views/VersionList.vue";
import IconList from "./views/IconList.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: GearList },
    { path: "/gear/:id", component: GearEdit, props: true },
    { path: "/keywords", component: KeywordList },
    { path: "/special-rules", component: SpecialRuleList },
    { path: "/locations", component: LocationList },
    { path: "/expansions", component: ExpansionList },
    { path: "/versions", component: VersionList },
    { path: "/icons", component: IconList },
  ],
});

export default router;
