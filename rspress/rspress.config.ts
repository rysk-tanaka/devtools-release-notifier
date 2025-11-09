import { defineConfig } from "rspress/config";

export default defineConfig({
  root: "docs",
  base: "/devtools-release-notifier/",
  title: "devtools-release-notifier",
  description: "Development tools release notifier documentation",
  logo: false,
  themeConfig: {
    socialLinks: [
      {
        icon: "github",
        mode: "link",
        content: "https://github.com/rysk/devtools-release-notifier",
      },
    ],
  },
  search: {
    versioned: false,
    codeBlocks: true,
  },
  markdown: {
    checkDeadLinks: false,
  },
});
