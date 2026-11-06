import { appendFileSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import semanticRelease from "semantic-release";

const repoRoot = process.cwd();
const stagingDirectory = join(repoRoot, ".release-staging");
const plannedVersionFile = join(stagingDirectory, "release-version");

mkdirSync(stagingDirectory, { recursive: true });
rmSync(plannedVersionFile, { force: true });

const result = await semanticRelease({ dryRun: true }, { cwd: repoRoot });
const version = result?.nextRelease?.version ?? "";

if (version) {
  writeFileSync(plannedVersionFile, `${version}\n`, "utf8");
  console.log(`Planned release version: ${version}`);
} else {
  console.log("No release is planned for this commit.");
}

if (process.env.GITHUB_OUTPUT) {
  appendFileSync(process.env.GITHUB_OUTPUT, `version=${version}\n`, "utf8");
}
