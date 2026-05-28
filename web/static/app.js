/**
 * 电子科技大学通知聚合系统 - 看板交互逻辑
 */

// 分类颜色映射（来自后端 config）
let categoryColors = {};

const app = Vue.createApp({
    data() {
        return {
            notices: [],
            stats: { total: 0, today_new: 0 },
            loading: false,
            // 筛选条件
            keyword: "",
            dateFrom: this.getDefaultDateFrom(),
            dateTo: "",
            activeCategories: [],
            activeSources: [],
            // 所有分类和来源（用于筛选标签）
            allCategories: [],
            allSources: [],
        };
    },

    created() {
        this.loadStats();
        this.loadSources();
        this.fetchNotices();
    },

    methods: {
        getDefaultDateFrom() {
            const d = new Date();
            d.setDate(d.getDate() - 14);
            return d.toISOString().slice(0, 10);
        },

        async loadStats() {
            try {
                const res = await fetch("/api/stats");
                const data = await res.json();
                this.stats = data;
                // 提取分类列表
                if (data.categories) {
                    this.allCategories = Object.keys(data.categories);
                }
            } catch (e) {
                console.error("加载统计失败:", e);
            }
        },

        async loadSources() {
            try {
                const res = await fetch("/api/sources");
                this.allSources = await res.json();
            } catch (e) {
                console.error("加载数据源失败:", e);
            }
        },

        async fetchNotices() {
            this.loading = true;
            try {
                const params = new URLSearchParams();
                params.set("date_from", this.dateFrom);
                if (this.dateTo) params.set("date_to", this.dateTo);
                if (this.keyword) params.set("keyword", this.keyword);
                if (this.activeCategories.length) params.set("categories", this.activeCategories.join(","));
                if (this.activeSources.length) params.set("sources", this.activeSources.join(","));
                params.set("limit", "200");

                const res = await fetch("/api/notices?" + params.toString());
                const data = await res.json();
                this.notices = data.notices || [];
            } catch (e) {
                console.error("加载通知失败:", e);
            } finally {
                this.loading = false;
            }
        },

        toggleCategory(cat) {
            const idx = this.activeCategories.indexOf(cat);
            if (idx >= 0) {
                this.activeCategories.splice(idx, 1);
            } else {
                this.activeCategories.push(cat);
            }
            this.fetchNotices();
        },

        toggleSource(sourceName) {
            const idx = this.activeSources.indexOf(sourceName);
            if (idx >= 0) {
                this.activeSources.splice(idx, 1);
            } else {
                this.activeSources.push(sourceName);
            }
            this.fetchNotices();
        },

        onSearch() {
            this.fetchNotices();
        },

        openLink(url) {
            if (url) {
                window.open(url, "_blank");
            }
        },

        isNew(notice) {
            return notice.is_new === 1;
        },

        getSourceColor(category) {
            if (!categoryColors[category]) {
                // 生成随机但稳定的颜色
                let hash = 0;
                for (let i = 0; i < category.length; i++) {
                    hash = category.charCodeAt(i) + ((hash << 5) - hash);
                }
                const h = Math.abs(hash) % 360;
                categoryColors[category] = `hsl(${h}, 55%, 48%)`;
            }
            return categoryColors[category];
        },

        formatDate(dateStr) {
            if (!dateStr) return "";
            return dateStr;
        },
    },
});

app.mount("#app");
