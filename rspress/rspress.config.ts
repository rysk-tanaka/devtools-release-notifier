import { defineConfig } from "rspress/config";
import mermaid from "rspress-plugin-mermaid";

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
        // Note: Update this URL manually if repository name changes
        content: "https://github.com/rysk-tanaka/devtools-release-notifier",
      },
    ],
  },
  search: {
    versioned: false,
    codeBlocks: true,
  },
  markdown: {
    // Disabled because documentation contains external links to GitHub files
    // which cannot be checked during build time without causing errors
    checkDeadLinks: false,
  },
  plugins: [mermaid()],
});
