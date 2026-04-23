(function () {
    function createItems(count, baseTitle, categories, imageName, actionText, basePrice) {
        var items = [];
        for (var i = 1; i <= count; i += 1) {
            var category = categories[(i - 1) % categories.length];
            items.push({
                id: i,
                title: baseTitle + " " + String.fromCharCode(64 + ((i - 1) % 26) + 1),
                subtitle: category + " 方案 " + i,
                description: "这是一个重复但不完全相同的说明块，用于展示 " + baseTitle + " 的重复标题、重复描述、重复标签和重复字段结构。",
                longDescription: "这是一个更长的说明块，用于展示 " + baseTitle + " 的重复标题、重复描述、重复标签和重复字段结构，同时保留足够多的相似词组、相似句式和相似属性名，以便观察预处理与编码阶段的效果。",
                category: category,
                tag: category,
                badge: i % 2 === 0 ? "重点" : "常规",
                image: imageName,
                price: basePrice + i * 17,
                actionText: actionText,
                highlight: i % 3 === 0 ? "推荐" : "标准"
            });
        }
        return items;
    }

    window.BenchmarkDataRich = {
        features: createItems(16, "功能模块", ["基础", "增强", "旗舰"], "images/banner.jpg", "查看亮点", 180),
        services: createItems(20, "服务模块", ["基础", "增强", "旗舰"], "images/banner.jpg", "查看服务", 220),
        cases: createItems(10, "案例模块", ["品牌", "产品", "活动"], "images/banner.jpg", "查看案例", 260),
        testimonials: createItems(8, "评价模块", ["长期客户", "新客户"], "images/avatar1.jpg", "查看评价", 0),
        team: createItems(8, "团队成员", ["策划", "研发", "测试", "设计"], "images/avatar2.jpg", "查看成员", 0),
        faq: createItems(12, "常见问题", ["FAQ"], "images/avatar3.jpg", "展开内容", 0),
        products: createItems(24, "产品模块", ["基础", "增强", "旗舰"], "images/gallery1.jpg", "立即购买", 320),
        bundles: createItems(8, "组合模块", ["基础", "增强", "旗舰"], "images/gallery2.jpg", "查看组合", 640),
        gallery: createItems(16, "画廊模块", ["品牌", "产品", "活动"], "images/gallery1.jpg", "查看预览", 0),
        reviews: createItems(8, "评论模块", ["品牌", "产品"], "images/avatar1.jpg", "查看反馈", 0),
        offices: createItems(6, "办公地点", ["华东", "华北", "华南"], "images/banner.jpg", "查看地址", 0),
        values: createItems(6, "价值观", ["协作", "稳定", "复用"], "images/logo.png", "查看说明", 0)
    };
}());
