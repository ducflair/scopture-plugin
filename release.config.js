/**
 * Semantic Release configuration
 * https://semantic-release.gitbook.io/semantic-release
 */
module.exports = {
  branches: ['main'],
  plugins: [
    // 1. Analyze commits using Conventional Commits
    '@semantic-release/commit-analyzer',

    // 2. Generate release notes from commits
    '@semantic-release/release-notes-generator',

    // 3. Verify the planned package version, publish to MCP Registry, and notify skills.sh on success
    [
      '@semantic-release/exec',
      {
        prepareCmd: 'python3 scripts/verify_release_plan.py --version ${nextRelease.version}',
        publishCmd:
          'python3 scripts/publish_mcp_registry.py --version ${nextRelease.version} || true',
        successCmd: 'npx --yes skills add ducflair/scopture-plugin --list || true',
      },
    ],

    // 4. Create git tag, GitHub Release, and upload release packages
    [
      '@semantic-release/github',
      {
        assets: [
          'dist/*.tar.gz',
          'dist/*.zip',
          'dist/*.pdf',
          'dist/checksums.txt',
          'server.json',
        ],
      },
    ],
  ],
};
